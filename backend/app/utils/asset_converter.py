"""
Asset conversion utility for the unified financial connection layer.
Handles conversions between different asset types including fiat, crypto, credit, etc.
"""
import random
from datetime import datetime, timedelta
from typing import Any

from ..models import AssetClass, ConversionType


class AssetConverter:
    """Handles conversions between different asset types."""

    # Mock exchange rates (in production, these would come from real APIs)
    FIAT_RATES = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 149.50,
        "CAD": 1.36,
        "AUD": 1.52,
        "CHF": 0.88,
        "CNY": 7.24
    }

    CRYPTO_PRICES_USD = {
        "BTC": 45000.00,
        "ETH": 2500.00,
        "USDC": 1.00,
        "USDT": 1.00,
        "DAI": 1.00,
        "SOL": 100.00,
        "MATIC": 0.85,
        "LINK": 15.00,
        "UNI": 6.50,
        "AAVE": 100.00
    }

    # Fee structures for different conversion types
    CONVERSION_FEES = {
        ConversionType.FIAT_TO_CRYPTO: {
            "percentage": 0.015,  # 1.5%
            "minimum": 0.99,
            "maximum": 49.99
        },
        ConversionType.CRYPTO_TO_FIAT: {
            "percentage": 0.015,  # 1.5%
            "minimum": 0.99,
            "maximum": 49.99
        },
        ConversionType.CRYPTO_TO_CRYPTO: {
            "percentage": 0.005,  # 0.5%
            "minimum": 0,
            "maximum": 25.00
        },
        ConversionType.CREDIT_TO_FIAT: {
            "percentage": 0.029,  # 2.9% (cash advance fee)
            "minimum": 10.00,
            "maximum": None
        },
        ConversionType.COLLATERAL_SWAP: {
            "percentage": 0.001,  # 0.1%
            "minimum": 5.00,
            "maximum": 100.00
        }
    }

    def __init__(self, data_manager=None):
        self.data_manager = data_manager
        self._rate_cache = {}
        self._cache_expiry = {}

    def get_conversion_rate(
        self,
        from_asset: str,
        to_asset: str,
        asset_class_from: AssetClass,
        asset_class_to: AssetClass
    ) -> tuple[float, datetime]:
        """Get conversion rate between two assets."""
        cache_key = f"{from_asset}_{to_asset}"

        # Check cache
        if cache_key in self._rate_cache:
            if datetime.utcnow() < self._cache_expiry.get(cache_key, datetime.min):
                return self._rate_cache[cache_key], self._cache_expiry[cache_key]

        # Calculate rate based on asset classes
        if asset_class_from == AssetClass.FIAT and asset_class_to == AssetClass.FIAT:
            rate = self._get_fiat_to_fiat_rate(from_asset, to_asset)
        elif asset_class_from == AssetClass.FIAT and asset_class_to == AssetClass.CRYPTO:
            rate = self._get_fiat_to_crypto_rate(from_asset, to_asset)
        elif asset_class_from == AssetClass.CRYPTO and asset_class_to == AssetClass.FIAT:
            rate = self._get_crypto_to_fiat_rate(from_asset, to_asset)
        elif asset_class_from == AssetClass.CRYPTO and asset_class_to == AssetClass.CRYPTO:
            rate = self._get_crypto_to_crypto_rate(from_asset, to_asset)
        elif asset_class_from == AssetClass.CREDIT:
            # Credit to fiat is 1:1 but with fees
            rate = 1.0
        else:
            # Default rate for unsupported conversions
            rate = 1.0

        # Add small market fluctuation
        rate = rate * (1 + random.uniform(-0.001, 0.001))

        # Cache the rate
        expiry = datetime.utcnow() + timedelta(minutes=5)
        self._rate_cache[cache_key] = rate
        self._cache_expiry[cache_key] = expiry

        return rate, expiry

    def _get_fiat_to_fiat_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two fiat currencies."""
        from_rate = self.FIAT_RATES.get(from_currency, 1.0)
        to_rate = self.FIAT_RATES.get(to_currency, 1.0)
        return to_rate / from_rate

    def _get_fiat_to_crypto_rate(self, from_currency: str, to_crypto: str) -> float:
        """Get rate from fiat to crypto."""
        # First convert to USD if needed
        fiat_to_usd = 1.0 / self.FIAT_RATES.get(from_currency, 1.0)
        # Then get crypto price in USD
        crypto_price = self.CRYPTO_PRICES_USD.get(to_crypto, 1.0)
        return fiat_to_usd / crypto_price

    def _get_crypto_to_fiat_rate(self, from_crypto: str, to_currency: str) -> float:
        """Get rate from crypto to fiat."""
        # Get crypto price in USD
        crypto_price = self.CRYPTO_PRICES_USD.get(from_crypto, 1.0)
        # Then convert to target currency
        usd_to_fiat = self.FIAT_RATES.get(to_currency, 1.0)
        return crypto_price * usd_to_fiat

    def _get_crypto_to_crypto_rate(self, from_crypto: str, to_crypto: str) -> float:
        """Get rate between two cryptocurrencies."""
        from_price = self.CRYPTO_PRICES_USD.get(from_crypto, 1.0)
        to_price = self.CRYPTO_PRICES_USD.get(to_crypto, 1.0)
        return from_price / to_price

    def calculate_conversion_fees(
        self,
        amount: float,
        conversion_type: ConversionType
    ) -> dict[str, float]:
        """Calculate fees for a conversion."""
        fee_structure = self.CONVERSION_FEES.get(conversion_type, {
            "percentage": 0.01,
            "minimum": 0,
            "maximum": None
        })

        # Calculate percentage fee
        percentage_fee = amount * fee_structure["percentage"]

        # Apply minimum/maximum
        if fee_structure["minimum"] is not None:
            percentage_fee = max(percentage_fee, fee_structure["minimum"])
        if fee_structure["maximum"] is not None:
            percentage_fee = min(percentage_fee, fee_structure["maximum"])

        # Additional fees based on conversion type
        network_fee = 0
        if conversion_type in [ConversionType.FIAT_TO_CRYPTO, ConversionType.CRYPTO_TO_FIAT]:
            network_fee = random.uniform(1.0, 5.0)  # Mock blockchain fee
        elif conversion_type == ConversionType.CRYPTO_TO_CRYPTO:
            network_fee = random.uniform(0.5, 3.0)  # Mock DEX fee

        return {
            "conversion_fee": round(percentage_fee, 2),
            "network_fee": round(network_fee, 2),
            "total_fee": round(percentage_fee + network_fee, 2)
        }

    def find_optimal_route(
        self,
        from_assets: list[dict[str, Any]],
        to_asset_class: AssetClass,
        amount_usd: float
    ) -> list[dict[str, Any]]:
        """Find the optimal route for a transfer considering fees and availability."""
        routes = []

        for asset in from_assets:
            # Check if asset has sufficient balance
            if asset["balance_usd"] < amount_usd:
                continue

            # Determine conversion type
            conversion_type = self._determine_conversion_type(
                AssetClass(asset["asset_class"]),
                to_asset_class
            )

            # Calculate fees
            fees = self.calculate_conversion_fees(amount_usd, conversion_type)

            # Calculate total cost
            total_cost = amount_usd + fees["total_fee"]

            # Estimate time
            if asset["asset_class"] == AssetClass.CRYPTO:
                estimated_time = random.randint(5, 30)  # minutes
            elif asset["asset_class"] == AssetClass.FIAT:
                if to_asset_class == AssetClass.CRYPTO:
                    estimated_time = random.randint(10, 60)  # minutes
                else:
                    estimated_time = random.randint(1, 3) * 1440  # days to minutes
            else:
                estimated_time = random.randint(60, 180)  # minutes

            routes.append({
                "source_asset": asset,
                "conversion_type": conversion_type.value,
                "fees": fees,
                "total_cost": total_cost,
                "estimated_time_minutes": estimated_time,
                "score": self._calculate_route_score(fees["total_fee"], estimated_time)
            })

        # Sort by score (lower is better)
        routes.sort(key=lambda x: x["score"])

        return routes

    def _determine_conversion_type(
        self,
        from_class: AssetClass,
        to_class: AssetClass
    ) -> ConversionType:
        """Determine the conversion type based on asset classes."""
        if from_class == AssetClass.FIAT and to_class == AssetClass.CRYPTO:
            return ConversionType.FIAT_TO_CRYPTO
        if from_class == AssetClass.CRYPTO and to_class == AssetClass.FIAT:
            return ConversionType.CRYPTO_TO_FIAT
        if from_class == AssetClass.CRYPTO and to_class == AssetClass.CRYPTO:
            return ConversionType.CRYPTO_TO_CRYPTO
        if from_class == AssetClass.CREDIT:
            return ConversionType.CREDIT_TO_FIAT
        # Default to fiat-to-crypto for unknown combinations
        return ConversionType.FIAT_TO_CRYPTO

    def _calculate_route_score(self, fee: float, time_minutes: int) -> float:
        """Calculate a score for route optimization (lower is better)."""
        # Weight fee more heavily than time
        fee_weight = 0.7
        time_weight = 0.3

        # Normalize time to hours
        time_hours = time_minutes / 60

        return (fee * fee_weight) + (time_hours * time_weight)

    def validate_collateral_value(
        self,
        collateral_assets: list[dict[str, Any]],
        required_value_usd: float,
        ltv_ratio: float = 0.5
    ) -> tuple[bool, float, str]:
        """Validate if collateral assets meet requirements."""
        total_value = 0

        for asset in collateral_assets:
            # Apply haircut based on asset volatility
            if asset["asset_class"] == AssetClass.CRYPTO:
                if asset["symbol"] in ["USDC", "USDT", "DAI"]:
                    haircut = 0.95  # 5% haircut for stablecoins
                else:
                    haircut = 0.8  # 20% haircut for volatile crypto
            elif asset["asset_class"] == AssetClass.NFT:
                haircut = 0.5  # 50% haircut for NFTs
            else:
                haircut = 0.9  # 10% haircut for other assets

            total_value += asset["value_usd"] * haircut

        # Check if collateral meets LTV requirements
        max_borrow = total_value * ltv_ratio
        is_valid = max_borrow >= required_value_usd

        message = "Sufficient collateral" if is_valid else "Insufficient collateral"
        if not is_valid:
            shortfall = required_value_usd - max_borrow
            message = f"Insufficient collateral. Need ${shortfall:.2f} more in collateral value"

        return is_valid, max_borrow, message

    def get_all_conversion_rates(self) -> dict[str, Any]:
        """Get all current conversion rates."""
        rates = {
            "fiat": self.FIAT_RATES.copy(),
            "crypto_usd": self.CRYPTO_PRICES_USD.copy(),
            "last_updated": datetime.utcnow().isoformat()
        }

        # Add some cross rates
        rates["popular_pairs"] = {
            "EUR/USD": 1 / self.FIAT_RATES["EUR"],
            "GBP/USD": 1 / self.FIAT_RATES["GBP"],
            "BTC/ETH": self.CRYPTO_PRICES_USD["BTC"] / self.CRYPTO_PRICES_USD["ETH"],
            "ETH/USDC": self.CRYPTO_PRICES_USD["ETH"] / self.CRYPTO_PRICES_USD["USDC"]
        }

        return rates
