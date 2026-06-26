"""
Live market-data streaming service.

Connects out (as a client) to a public, no-auth real-time market-data WebSocket
feed and ingests ticker updates into an in-process store. The default upstream is
the Coinbase Exchange feed (``wss://ws-feed.exchange.coinbase.com``), subscribing to
the ``ticker`` channel for a handful of crypto products.

Design goals / conventions (mirrors ``event_streaming.py``):
- Plain Python class with no FastAPI dependencies.
- Exposed as a single module-level global singleton at the bottom of the file.
- In-memory only: latest tick plus a small rolling history per product.
- Fully async, single-event-loop friendly (uses the async ``websockets`` client).
- Idempotent ``start()`` storing an ``asyncio.Task`` handle, plus an explicit
  ``stop()`` that cancels the task and closes the socket for graceful shutdown.
- Enterprise reconnect: exponential backoff with jitter, capped, never crashes the
  app when the feed is unreachable (graceful degradation to mock pricing upstream).

The natural sink is the in-process store; the investments domain reads live prices
from this singleton and falls back to its existing mock generator when a quote is
missing or stale, so the application keeps working fully offline.
"""
import asyncio
import contextlib
import json
import logging
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ..core.config import settings

logger = logging.getLogger(__name__)


# Map BankFlow internal asset symbols (data_manager.crypto_assets) to upstream
# product IDs on the live feed. The feed is crypto-only, so equities/ETFs are not
# covered here and transparently fall back to the existing mock generator.
SYMBOL_TO_PRODUCT: dict[str, str] = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "ADA": "ADA-USD",
    "DOT": "DOT-USD",
    "BNB": "BNB-USD",
}
PRODUCT_TO_SYMBOL: dict[str, str] = {v: k for k, v in SYMBOL_TO_PRODUCT.items()}


@dataclass
class MarketTick:
    """A single normalized live market-data tick for one product."""

    product_id: str
    symbol: str
    price: float
    bid: float
    ask: float
    open_24h: float
    high_24h: float
    low_24h: float
    volume_24h: float
    timestamp: datetime
    # When this tick was ingested locally. Freshness is measured from receipt
    # (i.e. "is the feed alive") rather than the upstream exchange time. Set by
    # the store on update().
    received_at: datetime | None = None

    def age_seconds(self, now: datetime | None = None) -> float:
        """Seconds since this tick was received locally."""
        now = now or datetime.now(UTC)
        reference = self.received_at or self.timestamp
        return (now - reference).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_id": self.product_id,
            "symbol": self.symbol,
            "price": self.price,
            "bid": self.bid,
            "ask": self.ask,
            "open_24h": self.open_24h,
            "high_24h": self.high_24h,
            "low_24h": self.low_24h,
            "volume_24h": self.volume_24h,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MarketDataStore:
    """In-memory store of the latest tick plus a small rolling history per product."""

    history_size: int = 120
    staleness_seconds: float = 30.0
    _latest: dict[str, MarketTick] = field(default_factory=dict)
    _history: dict[str, deque] = field(default_factory=dict)
    last_update: datetime | None = None

    def update(self, tick: MarketTick) -> None:
        """Record a new tick as the latest value and append to rolling history."""
        now = datetime.now(UTC)
        if tick.received_at is None:
            tick.received_at = now
        self._latest[tick.product_id] = tick
        if tick.product_id not in self._history:
            self._history[tick.product_id] = deque(maxlen=self.history_size)
        self._history[tick.product_id].append(tick)
        self.last_update = now

    def get_latest(self, product_id: str) -> MarketTick | None:
        """Return the most recent tick for a product, if any."""
        return self._latest.get(product_id)

    def get_history(self, product_id: str) -> list[MarketTick]:
        """Return the rolling history (oldest first) for a product."""
        return list(self._history.get(product_id, []))

    def is_fresh(self, product_id: str, now: datetime | None = None) -> bool:
        """Whether a fresh (non-stale) live tick exists for the product."""
        tick = self._latest.get(product_id)
        if tick is None:
            return False
        return tick.age_seconds(now) <= self.staleness_seconds

    def get_fresh_price(self, symbol: str) -> float | None:
        """
        Return the latest live price for a BankFlow symbol (e.g. ``BTC``) if a
        fresh quote exists, otherwise ``None`` so callers can fall back to mock data.
        """
        product_id = SYMBOL_TO_PRODUCT.get(symbol.upper())
        if not product_id or not self.is_fresh(product_id):
            return None
        tick = self._latest.get(product_id)
        return tick.price if tick else None


class MarketDataStreamService:
    """Long-running client that ingests a live market-data WebSocket feed."""

    def __init__(
        self,
        *,
        source_url: str | None = None,
        products: list[str] | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.source_url = source_url or settings.market_data_source_url
        self.products = list(products if products is not None else settings.market_data_products)
        self.enabled = settings.market_data_enabled if enabled is None else enabled
        self.reconnect_min = settings.market_data_reconnect_min_seconds
        self.reconnect_max = settings.market_data_reconnect_max_seconds

        self.store = MarketDataStore(
            history_size=settings.market_data_history_size,
            staleness_seconds=settings.market_data_staleness_seconds,
        )

        self._task: asyncio.Task | None = None
        self._running = False
        self._connected = False
        self._connection_attempts = 0
        self._messages_ingested = 0
        self._last_error: str | None = None

    # ------------------------------------------------------------------ lifecycle
    async def start(self) -> None:
        """Start the ingestion loop (idempotent). No-op when disabled."""
        if not self.enabled:
            logger.info("Market data streaming disabled by configuration; using mock prices")
            return
        if self._task is not None and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._ingest_loop())
        logger.info(
            "Market data streaming service started",
            extra={"source_url": self.source_url, "products": self.products},
        )

    async def stop(self) -> None:
        """Cancel the ingestion loop and close the socket for graceful shutdown."""
        self._running = False
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        self._connected = False
        logger.info("Market data streaming service stopped")

    # ------------------------------------------------------------------- ingestion
    def _build_subscribe_message(self) -> str:
        """Build the Coinbase Exchange ticker subscription frame."""
        return json.dumps(
            {
                "type": "subscribe",
                "product_ids": self.products,
                "channels": ["ticker"],
            }
        )

    def _handle_message(self, raw: str | bytes) -> bool:
        """
        Parse a single inbound frame and update the store.

        Returns ``True`` when a ticker tick was ingested, ``False`` otherwise
        (subscriptions, heartbeats, errors, malformed frames). Pure/sync so it is
        trivially unit-testable without a network.
        """
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            logger.warning("Discarding malformed market-data frame")
            return False

        if not isinstance(data, dict):
            return False

        msg_type = data.get("type")
        if msg_type == "error":
            self._last_error = data.get("message", "feed error")
            logger.error(f"Market-data feed error: {self._last_error}")
            return False
        if msg_type != "ticker":
            # subscriptions / heartbeats / snapshots are ignored
            return False

        product_id = data.get("product_id")
        price = data.get("price")
        if not product_id or price is None:
            return False

        try:
            tick = MarketTick(
                product_id=product_id,
                symbol=PRODUCT_TO_SYMBOL.get(product_id, product_id.split("-")[0]),
                price=float(price),
                bid=float(data.get("best_bid") or price),
                ask=float(data.get("best_ask") or price),
                open_24h=float(data.get("open_24h") or price),
                high_24h=float(data.get("high_24h") or price),
                low_24h=float(data.get("low_24h") or price),
                volume_24h=float(data.get("volume_24h") or 0.0),
                timestamp=self._parse_timestamp(data.get("time")),
            )
        except (ValueError, TypeError) as exc:
            logger.warning(f"Discarding unparseable ticker frame: {exc}")
            return False

        self.store.update(tick)
        self._messages_ingested += 1
        return True

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        """Parse an upstream ISO-8601 timestamp, defaulting to now (UTC)."""
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
                return parsed
            except ValueError:
                pass
        return datetime.now(UTC)

    async def _run_connection(self) -> None:
        """
        Open one connection session: subscribe and consume frames until the socket
        closes. Separated from the reconnect loop so it can be unit-tested with a
        fake connection and so the loop logic stays simple.
        """
        # Imported lazily so a missing optional dependency never breaks app import.
        import websockets

        async with websockets.connect(
            self.source_url,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=5,
            max_queue=1024,
        ) as ws:
            await ws.send(self._build_subscribe_message())
            self._connected = True
            self._connection_attempts = 0
            self._last_error = None
            logger.info(
                "Connected to live market-data feed",
                extra={"source_url": self.source_url, "products": self.products},
            )
            async for raw in ws:
                self._handle_message(raw)

    async def _ingest_loop(self) -> None:
        """Reconnect loop with exponential backoff + jitter. Never raises out."""
        backoff = self.reconnect_min
        while self._running:
            self._connection_attempts += 1
            try:
                await self._run_connection()
                # Clean socket close: reset backoff before reconnecting.
                backoff = self.reconnect_min
            except asyncio.CancelledError:
                # Cooperative shutdown from stop().
                raise
            except Exception as exc:  # never let the feed crash the app
                self._connected = False
                self._last_error = str(exc)
                logger.error(
                    f"Live market-data feed disconnected, reconnecting: {exc}",
                    exc_info=True,
                    extra={"backoff_seconds": round(backoff, 2)},
                )
            finally:
                self._connected = False

            if not self._running:
                break

            # Backoff with jitter, capped at the configured maximum.
            sleep_for = min(backoff, self.reconnect_max)
            sleep_for += random.uniform(0, sleep_for * 0.25)
            with contextlib.suppress(asyncio.CancelledError):
                await asyncio.sleep(sleep_for)
            backoff = min(backoff * 2, self.reconnect_max)

    # ----------------------------------------------------------------- public API
    def get_live_price(self, symbol: str) -> float | None:
        """Latest fresh live price for a BankFlow symbol, or ``None``."""
        return self.store.get_fresh_price(symbol)

    def get_live_quote(self, symbol: str) -> MarketTick | None:
        """Latest fresh live tick for a BankFlow symbol, or ``None``."""
        product_id = SYMBOL_TO_PRODUCT.get(symbol.upper())
        if not product_id or not self.store.is_fresh(product_id):
            return None
        return self.store.get_latest(product_id)

    def get_status(self) -> dict[str, Any]:
        """Operational status snapshot for monitoring / status endpoints."""
        now = datetime.now(UTC)
        products_status = []
        for product_id in self.products:
            tick = self.store.get_latest(product_id)
            products_status.append(
                {
                    "product_id": product_id,
                    "symbol": PRODUCT_TO_SYMBOL.get(product_id, product_id.split("-")[0]),
                    "last_price": tick.price if tick else None,
                    "fresh": self.store.is_fresh(product_id, now),
                    "age_seconds": round(tick.age_seconds(now), 3) if tick else None,
                }
            )
        return {
            "enabled": self.enabled,
            "connected": self._connected,
            "source_url": self.source_url,
            "products": self.products,
            "connection_attempts": self._connection_attempts,
            "messages_ingested": self._messages_ingested,
            "last_update": self.store.last_update.isoformat() if self.store.last_update else None,
            "last_error": self._last_error,
            "products_status": products_status,
        }


# Global market data streaming service instance
market_data_stream_service = MarketDataStreamService()
