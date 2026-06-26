"""
Tests for the live market-data streaming service and its integration with the
investments domain.

These tests MOCK the WebSocket feed entirely -- no live network is opened -- so the
suite stays deterministic and CI-friendly. They cover:
  * tick ingestion / parsing into the in-memory store (rolling history + staleness)
  * the reconnect loop driven through a fake (in-process) websockets connection
  * investment valuation using a live price (mark-to-market re-mark)
  * graceful fallback to mock pricing when the feed is offline / stale
"""
import asyncio
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.repositories.data_manager import data_manager
from app.repositories.investment_manager import InvestmentManager
from app.services.market_data_stream import (
    MarketDataStore,
    MarketDataStreamService,
    MarketTick,
)


def _ticker_frame(product_id: str = "BTC-USD", price: str = "50000.00") -> str:
    """Build a Coinbase-style ticker frame."""
    return json.dumps({
        "type": "ticker",
        "product_id": product_id,
        "price": price,
        "best_bid": str(float(price) - 1),
        "best_ask": str(float(price) + 1),
        "open_24h": "49000.00",
        "high_24h": "51000.00",
        "low_24h": "48000.00",
        "volume_24h": "1234.56",
        "time": "2026-06-26T12:00:00.000000Z",
    })


class _FakeWebSocket:
    """Minimal async websocket connection yielding canned frames then closing."""

    def __init__(self, frames):
        self._frames = list(frames)
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def send(self, message):
        self.sent.append(message)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._frames:
            raise StopAsyncIteration
        return self._frames.pop(0)


class TestMarketDataIngestion:
    """Frame parsing and store updates (no network)."""

    def test_handle_ticker_frame_updates_store(self):
        service = MarketDataStreamService(products=["BTC-USD"], enabled=True)
        ingested = service._handle_message(_ticker_frame("BTC-USD", "50000.00"))

        assert ingested is True
        tick = service.store.get_latest("BTC-USD")
        assert tick is not None
        assert tick.price == 50000.00
        assert tick.symbol == "BTC"
        assert tick.bid == 49999.00
        assert tick.ask == 50001.00
        # Live price is exposed via the BankFlow symbol mapping.
        assert service.get_live_price("BTC") == 50000.00

    def test_non_ticker_frames_are_ignored(self):
        service = MarketDataStreamService(products=["BTC-USD"], enabled=True)
        assert service._handle_message(json.dumps({"type": "subscriptions"})) is False
        assert service._handle_message(json.dumps({"type": "heartbeat"})) is False
        assert service.store.get_latest("BTC-USD") is None

    def test_malformed_frame_does_not_raise(self):
        service = MarketDataStreamService(products=["BTC-USD"], enabled=True)
        assert service._handle_message("{not-json") is False
        assert service._handle_message(json.dumps(["a", "list"])) is False

    def test_rolling_history_is_bounded(self):
        store = MarketDataStore(history_size=3, staleness_seconds=30)
        for price in (1.0, 2.0, 3.0, 4.0):
            store.update(MarketTick(
                product_id="ETH-USD", symbol="ETH", price=price, bid=price, ask=price,
                open_24h=price, high_24h=price, low_24h=price, volume_24h=1.0,
                timestamp=datetime.now(UTC),
            ))
        history = store.get_history("ETH-USD")
        assert len(history) == 3
        assert [t.price for t in history] == [2.0, 3.0, 4.0]

    def test_stale_tick_is_not_fresh(self):
        store = MarketDataStore(history_size=10, staleness_seconds=30)
        old = datetime.now(UTC) - timedelta(seconds=120)
        store.update(MarketTick(
            product_id="BTC-USD", symbol="BTC", price=10.0, bid=10.0, ask=10.0,
            open_24h=10.0, high_24h=10.0, low_24h=10.0, volume_24h=1.0,
            timestamp=old, received_at=old,
        ))
        assert store.is_fresh("BTC-USD") is False
        assert store.get_fresh_price("BTC") is None


class TestReconnectLoop:
    """The ingestion loop drives a fake connection with no real socket."""

    def test_run_connection_subscribes_and_ingests(self):
        service = MarketDataStreamService(products=["BTC-USD"], enabled=True)
        fake_ws = _FakeWebSocket([_ticker_frame("BTC-USD", "60000.00")])

        with patch("websockets.connect", return_value=fake_ws):
            asyncio.run(service._run_connection())

        # It sent a subscribe frame for the configured products.
        assert len(fake_ws.sent) == 1
        sub = json.loads(fake_ws.sent[0])
        assert sub["type"] == "subscribe"
        assert sub["product_ids"] == ["BTC-USD"]
        # And ingested the canned tick.
        assert service.get_live_price("BTC") == 60000.00

    def test_ingest_loop_recovers_from_connection_error(self):
        service = MarketDataStreamService(products=["BTC-USD"], enabled=True)
        service.reconnect_min = 0.0
        service.reconnect_max = 0.0

        calls = {"n": 0}

        async def fake_run_connection():
            calls["n"] += 1
            if calls["n"] == 1:
                raise ConnectionError("boom")
            # Second attempt succeeds, ingest a tick then stop the loop.
            service._handle_message(_ticker_frame("BTC-USD", "70000.00"))
            service._running = False

        async def driver():
            service._running = True
            with patch.object(service, "_run_connection", side_effect=fake_run_connection):
                await service._ingest_loop()

        asyncio.run(asyncio.wait_for(driver(), timeout=5))

        assert calls["n"] == 2  # reconnected after the first failure
        assert service.get_live_price("BTC") == 70000.00

    def test_start_is_noop_when_disabled(self):
        service = MarketDataStreamService(products=["BTC-USD"], enabled=False)
        asyncio.run(service.start())
        assert service._task is None


class TestLiveValuationIntegration:
    """InvestmentManager uses live prices and falls back to mock pricing."""

    def _seed_crypto_position(self, symbol="BTC"):
        """Create an isolated account/portfolio/position holding a crypto symbol."""
        user = next((u for u in data_manager.users), None)
        assert user is not None
        account_id = max((a['id'] for a in data_manager.investment_accounts), default=0) + 1000
        portfolio_id = max((p['id'] for p in data_manager.investment_portfolios), default=0) + 1000
        position_id = max((p['id'] for p in data_manager.investment_positions), default=0) + 1000

        data_manager.investment_accounts.append({
            'id': account_id, 'user_id': user['id'], 'account_type': 'individual',
            'account_number': f'INV-{account_id}', 'account_name': 'Live Test Account',
            'balance': 100000.0, 'buying_power': 90000.0, 'portfolio_value': 100000.0,
            'total_return': 0.0, 'total_return_percent': 0.0, 'is_retirement': False,
            'risk_tolerance': 'moderate', 'created_at': datetime.now(UTC),
            'updated_at': datetime.now(UTC),
        })
        data_manager.investment_portfolios.append({
            'id': portfolio_id, 'account_id': account_id, 'name': 'Live Test Portfolio',
            'risk_level': 'moderate', 'total_value': 100000.0, 'total_cost_basis': 100000.0,
            'created_at': datetime.now(UTC),
        })
        data_manager.investment_positions.append({
            'id': position_id, 'portfolio_id': portfolio_id, 'asset_type': 'crypto',
            'asset_id': None, 'symbol': symbol, 'shares': 2.0,
            'cost_basis': 80000.0, 'current_value': 80000.0, 'realized_gains': 0.0,
            'first_purchase_date': datetime.now(UTC).date(),
        })
        return user['id'], account_id, portfolio_id, position_id

    def _service_with_live_price(self, symbol, product_id, price):
        service = MarketDataStreamService(products=[product_id], enabled=True)
        service.store.update(MarketTick(
            product_id=product_id, symbol=symbol, price=price, bid=price - 1, ask=price + 1,
            open_24h=price, high_24h=price, low_24h=price, volume_24h=10.0,
            timestamp=datetime.now(UTC),
        ))
        service._connected = True
        return service

    def test_get_market_data_prefers_live_price(self):
        service = self._service_with_live_price("BTC", "BTC-USD", 65000.0)
        manager = InvestmentManager(data_manager, market_data_service=service)

        md = manager.get_market_data("BTC")
        assert float(md.last_price) == 65000.0

    def test_get_market_data_falls_back_to_mock_offline(self):
        # Empty store -> no fresh quote -> mock generator used, never raises.
        service = MarketDataStreamService(products=["BTC-USD"], enabled=True)
        manager = InvestmentManager(data_manager, market_data_service=service)

        md = manager.get_market_data("BTC")
        # Mock price derives from the seeded crypto base price (42850), not the live value.
        assert float(md.last_price) > 0
        assert float(md.last_price) != 65000.0

    def test_live_valuation_marks_position_to_market(self):
        user_id, account_id, _portfolio_id, _position_id = self._seed_crypto_position("BTC")
        service = self._service_with_live_price("BTC", "BTC-USD", 65000.0)
        manager = InvestmentManager(data_manager, market_data_service=service)

        valuation = manager.get_live_portfolio_valuation(account_id, user_id)
        assert valuation is not None
        assert valuation['live_priced_count'] == 1
        assert valuation['feed_connected'] is True
        # 2 shares * 65000 live price = 130000.
        assert valuation['total_value'] == 130000.0
        holding = valuation['holdings'][0]
        assert holding['price_source'] == 'live'
        assert holding['current_value'] == 130000.0

    def test_live_valuation_falls_back_when_feed_offline(self):
        user_id, account_id, _portfolio_id, _position_id = self._seed_crypto_position("ETH")
        # Feed has no quote for ETH -> mock fallback, stored current_value used.
        service = MarketDataStreamService(products=["BTC-USD"], enabled=True)
        manager = InvestmentManager(data_manager, market_data_service=service)

        valuation = manager.get_live_portfolio_valuation(account_id, user_id)
        assert valuation is not None
        assert valuation['live_priced_count'] == 0
        assert valuation['mock_priced_count'] == 1
        holding = valuation['holdings'][0]
        assert holding['price_source'] == 'mock'
        assert holding['current_value'] == 80000.0


class TestLiveMarketDataEndpoints:
    """Route-level coverage via the in-process TestClient (no network)."""

    def test_live_market_data_endpoint_mock_fallback(self, client, auth_headers):
        resp = client.get("/api/investments/market-data/live/AAPL", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        # No live feed connected in tests -> graceful mock fallback.
        assert body["is_live"] is False
        assert body["source"] == "mock_fallback"
        assert body["price"] > 0

    def test_stream_status_endpoint(self, client, auth_headers):
        resp = client.get("/api/investments/market-data/stream/status", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "enabled" in body
        assert "connected" in body
        assert "products" in body
