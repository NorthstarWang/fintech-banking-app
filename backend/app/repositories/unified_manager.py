"""
Unified financial manager for cross-asset operations and aggregations.
"""
import random
from datetime import datetime
from typing import Any

from ..models import AssetBridge, AssetClass, CollateralPosition, ConversionRate, UnifiedBalance, UnifiedTransferStatus
from ..utils.asset_converter import AssetConverter


class UnifiedManager:
    """Manager for unified financial operations across all asset types."""

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.asset_converter = AssetConverter(data_manager)

    def calculate_unified_balance(self, user_id: int) -> UnifiedBalance:
        """Calculate and store unified balance for a user."""
        # Initialize totals
        total_net_worth = 0.0
        fiat_assets = {}
        total_fiat = 0.0
        crypto_assets = {}
        total_crypto = 0.0
        nft_value = 0.0
        credit_available = 0.0
        credit_used = 0.0
        total_loans = 0.0
        monthly_obligations = 0.0
        coverage_amount = 0.0
        insurance_types = set()
        defi_value = 0.0
        defi_yield = 0.0

        # Calculate fiat assets
        user_accounts = [a for a in self.data_manager.accounts if a.get('user_id') == user_id]
        for account in user_accounts:
            balance = account.get('balance', 0)
            currency = account.get('currency', 'USD')

            if currency not in fiat_assets:
                fiat_assets[currency] = 0
            fiat_assets[currency] += balance

            # Convert to USD
            rate = self.asset_converter.FIAT_RATES.get(currency, 1.0)
            usd_value = balance / rate
            total_fiat += usd_value

            # Add credit info
            if account.get('account_type') == 'credit_card':
                limit = account.get('credit_limit', 0)
                credit_available += (limit - balance)
                credit_used += balance

        # Calculate crypto assets
        user_wallets = [w for w in self.data_manager.crypto_wallets if w.get('user_id') == user_id]
        for wallet in user_wallets:
            wallet_assets = [a for a in self.data_manager.crypto_assets if a.get('wallet_id') == wallet['id']]

            for asset in wallet_assets:
                symbol = asset.get('symbol')
                balance = float(asset.get('balance', 0))
                usd_value = asset.get('usd_value', 0)

                if symbol not in crypto_assets:
                    crypto_assets[symbol] = {
                        'amount': 0,
                        'usd_value': 0
                    }

                crypto_assets[symbol]['amount'] += balance
                crypto_assets[symbol]['usd_value'] += usd_value
                total_crypto += usd_value

            # NFT values
            wallet_nfts = [n for n in self.data_manager.nft_assets if n.get('wallet_id') == wallet['id']]
            for nft in wallet_nfts:
                nft_value += nft.get('estimated_value_usd', 0)

            # DeFi positions
            wallet_defi = [d for d in self.data_manager.defi_positions if d.get('wallet_id') == wallet['id']]
            for position in wallet_defi:
                defi_value += position.get('usd_value', 0)
                # Calculate annual yield
                apy = position.get('apy', 0)
                position_value = position.get('usd_value', 0)
                defi_yield += (position_value * apy / 100)

        # Get loan information (mock for now as loan models not in memory_models yet)
        # This would aggregate from loan_manager when available
        total_loans = random.uniform(0, 50000) if random.random() > 0.7 else 0
        if total_loans > 0:
            monthly_obligations = total_loans * 0.05  # Assume 5% monthly payment

        # Get insurance information (mock for now)
        # This would aggregate from insurance_manager when available
        if random.random() > 0.5:
            insurance_types = ["health", "auto", "home"]
            coverage_amount = random.uniform(100000, 500000)

        # Calculate metrics
        total_assets = total_fiat + total_crypto + nft_value + defi_value
        total_liabilities = credit_used + total_loans
        total_net_worth = total_assets - total_liabilities

        debt_to_asset_ratio = total_liabilities / total_assets if total_assets > 0 else 0

        # Liquid vs illiquid
        liquid_assets = total_fiat + total_crypto + defi_value
        illiquid_assets = nft_value

        # Create and store unified balance
        unified_balance = UnifiedBalance(
            user_id=user_id,
            total_net_worth_usd=total_net_worth,
            fiat_assets=fiat_assets,
            total_fiat_usd=total_fiat,
            crypto_assets=crypto_assets,
            nft_collection_value=nft_value,
            total_crypto_usd=total_crypto,
            total_credit_available=credit_available,
            credit_utilization=credit_used / (credit_used + credit_available) if (credit_used + credit_available) > 0 else 0,
            total_loans=total_loans,
            total_monthly_obligations=monthly_obligations,
            total_coverage_amount=coverage_amount,
            insurance_types_covered=list(insurance_types),
            defi_positions_value=defi_value,
            defi_yield_annual=defi_yield,
            debt_to_asset_ratio=debt_to_asset_ratio,
            liquid_assets=liquid_assets,
            illiquid_assets=illiquid_assets,
            last_updated=datetime.utcnow()
        )

        # Store in data manager
        self.data_manager.unified_balances.append(unified_balance.to_dict())

        return unified_balance

    def create_asset_bridge(
        self,
        user_id: int,
        from_asset_class: AssetClass,
        from_asset_id: str,
        from_amount: float,
        to_asset_class: AssetClass,
        to_asset_id: str | None = None,
        to_asset_type: str | None = None
    ) -> AssetBridge:
        """Create an asset bridge for conversion between different asset types."""
        # Determine conversion type
        conversion_type = self.asset_converter._determine_conversion_type(
            from_asset_class, to_asset_class
        )

        # Get asset details
        from_asset_name = self._get_asset_name(from_asset_class, from_asset_id)
        to_asset_name = self._get_asset_name(to_asset_class, to_asset_id, to_asset_type)

        # Get conversion rate
        rate, _ = self.asset_converter.get_conversion_rate(
            from_asset_name.split()[-1],  # Get currency/symbol
            to_asset_name.split()[-1],
            from_asset_class,
            to_asset_class
        )

        # Calculate amounts and fees
        to_amount = from_amount * rate
        fees = self.asset_converter.calculate_conversion_fees(from_amount, conversion_type)

        # Create bridge
        bridge = AssetBridge(
            user_id=user_id,
            bridge_type=conversion_type.value,
            from_asset_class=from_asset_class.value,
            from_asset_id=from_asset_id,
            from_amount=str(from_amount),
            from_asset_name=from_asset_name,
            to_asset_class=to_asset_class.value,
            to_asset_id=to_asset_id or self._generate_asset_id(to_asset_class),
            to_amount=str(to_amount - fees['total_fee']),
            to_asset_name=to_asset_name,
            exchange_rate=rate,
            fees=fees,
            total_fees_usd=fees['total_fee'],
            status=UnifiedTransferStatus.PENDING,
            initiated_at=datetime.utcnow()
        )

        # Store in data manager
        self.data_manager.asset_bridges.append(bridge.to_dict())

        # Simulate processing
        self._process_bridge(bridge)

        return bridge

    def _get_asset_name(
        self,
        asset_class: AssetClass,
        asset_id: str | None,
        asset_type: str | None = None
    ) -> str:
        """Get human-readable asset name."""
        if asset_class == AssetClass.FIAT:
            if asset_id:
                account = next((a for a in self.data_manager.accounts if str(a['id']) == asset_id), None)
                if account:
                    return f"{account['name']} ({account.get('currency', 'USD')})"
            return f"Fiat Account ({asset_type or 'USD'})"

        if asset_class == AssetClass.CRYPTO:
            if asset_id:
                wallet = next((w for w in self.data_manager.crypto_wallets if str(w['id']) == asset_id), None)
                if wallet:
                    return f"{wallet['name']} ({asset_type or 'ETH'})"
            return f"Crypto Wallet ({asset_type or 'ETH'})"

        if asset_class == AssetClass.CREDIT:
            if asset_id:
                card = next((c for c in self.data_manager.cards if str(c['id']) == asset_id), None)
                if card:
                    return f"Card ending {card.get('last_four', 'XXXX')}"
            return "Credit Card"

        return f"{asset_class.value.title()} Asset"

    def _generate_asset_id(self, asset_class: AssetClass) -> str:
        """Generate a new asset ID based on class."""
        if asset_class == AssetClass.FIAT:
            # Would create a new account
            return f"acc_{len(self.data_manager.accounts) + 1}"
        if asset_class == AssetClass.CRYPTO:
            # Would create a new wallet
            return f"wallet_{len(self.data_manager.crypto_wallets) + 1}"
        return f"{asset_class.value}_{datetime.utcnow().timestamp()}"

    def _process_bridge(self, bridge: AssetBridge):
        """Simulate processing of asset bridge."""
        # In production, this would handle actual transfers
        # For now, just update status after a delay
        bridge.status = UnifiedTransferStatus.COMPLETED
        bridge.completed_at = datetime.utcnow()

        # Update in data manager
        for b in self.data_manager.asset_bridges:
            if b['id'] == bridge.id:
                b['status'] = bridge.status if isinstance(bridge.status, str) else bridge.status.value
                b['completed_at'] = bridge.completed_at
                break

    def find_optimal_transfer_route(
        self,
        user_id: int,
        recipient_identifier: str,
        amount_usd: float,
        preferred_method: str | None = None
    ) -> dict[str, Any]:
        """Find the optimal route for a transfer."""
        # Get user's available assets
        available_assets = self._get_user_available_assets(user_id)

        # Determine recipient type and preferred destination
        recipient_type = self._identify_recipient_type(recipient_identifier)

        # Get possible routes
        routes = self.asset_converter.find_optimal_route(
            available_assets,
            recipient_type['preferred_asset_class'],
            amount_usd
        )

        if not routes:
            return {
                "error": "No viable route found",
                "reason": "Insufficient funds or no compatible assets"
            }

        # Select best route (first one is optimal)
        best_route = routes[0]

        return {
            "recipient_type": recipient_type,
            "recommended_route": best_route,
            "alternative_routes": routes[1:3],  # Top 3 alternatives
            "estimated_total_cost": best_route['total_cost'],
            "estimated_time": best_route['estimated_time_minutes']
        }

    def _get_user_available_assets(self, user_id: int) -> list[dict[str, Any]]:
        """Get all available assets for a user with their balances."""
        assets = []

        # Fiat accounts
        accounts = [a for a in self.data_manager.accounts if a.get('user_id') == user_id]
        for account in accounts:
            if account.get('account_type') != 'credit_card':
                assets.append({
                    'asset_class': AssetClass.FIAT,
                    'asset_id': account['id'],
                    'name': account['name'],
                    'currency': account.get('currency', 'USD'),
                    'balance': account.get('balance', 0),
                    'balance_usd': account.get('balance', 0) / self.asset_converter.FIAT_RATES.get(
                        account.get('currency', 'USD'), 1.0
                    )
                })

        # Crypto assets
        wallets = [w for w in self.data_manager.crypto_wallets if w.get('user_id') == user_id]
        for wallet in wallets:
            wallet_value = 0
            wallet_assets = [a for a in self.data_manager.crypto_assets if a.get('wallet_id') == wallet['id']]

            for crypto_asset in wallet_assets:
                wallet_value += crypto_asset.get('usd_value', 0)

            if wallet_value > 0:
                assets.append({
                    'asset_class': AssetClass.CRYPTO,
                    'asset_id': wallet['id'],
                    'name': wallet['name'],
                    'network': wallet['network'],
                    'balance_usd': wallet_value
                })

        # Available credit
        credit_available = 0
        for account in accounts:
            if account.get('account_type') == 'credit_card':
                limit = account.get('credit_limit', 0)
                balance = account.get('balance', 0)
                available = limit - balance
                if available > 0:
                    credit_available += available

        if credit_available > 0:
            assets.append({
                'asset_class': AssetClass.CREDIT,
                'asset_id': 'combined_credit',
                'name': 'Available Credit',
                'balance_usd': credit_available
            })

        return assets

    def _identify_recipient_type(self, identifier: str) -> dict[str, Any]:
        """Identify recipient type from identifier."""
        # Email pattern
        if '@' in identifier:
            return {
                'type': 'email',
                'preferred_asset_class': AssetClass.FIAT,
                'preferred_method': 'bank_transfer'
            }

        # Crypto address patterns
        if identifier.startswith('0x') and len(identifier) == 42:
            return {
                'type': 'ethereum_address',
                'preferred_asset_class': AssetClass.CRYPTO,
                'preferred_method': 'crypto_transfer'
            }

        if identifier.startswith('bc1') or (identifier[0] in '13' and len(identifier) > 26):
            return {
                'type': 'bitcoin_address',
                'preferred_asset_class': AssetClass.CRYPTO,
                'preferred_method': 'crypto_transfer'
            }

        # Username (internal user)
        user = next((u for u in self.data_manager.users if u['username'] == identifier), None)
        if user:
            return {
                'type': 'internal_user',
                'user_id': user['id'],
                'preferred_asset_class': AssetClass.FIAT,
                'preferred_method': 'internal_transfer'
            }

        # Default to external bank account
        return {
            'type': 'external_account',
            'preferred_asset_class': AssetClass.FIAT,
            'preferred_method': 'wire_transfer'
        }

    def create_collateral_position(
        self,
        user_id: int,
        collateral_assets: list[dict[str, Any]],
        borrow_amount: float,
        currency: str = "USD",
        position_type: str = "loan"
    ) -> CollateralPosition:
        """Create a cross-asset collateral position."""
        # Validate collateral
        is_valid, max_borrow, message = self.asset_converter.validate_collateral_value(
            collateral_assets,
            borrow_amount,
            ltv_ratio=0.5
        )

        if not is_valid:
            raise ValueError(message)

        # Calculate total collateral value
        total_collateral = sum(asset['value_usd'] for asset in collateral_assets)

        # Create position
        position = CollateralPosition(
            user_id=user_id,
            position_type=position_type,
            collateral_assets=collateral_assets,
            total_collateral_value_usd=total_collateral,
            amount_borrowed=borrow_amount,
            currency_borrowed=currency,
            loan_to_value=borrow_amount / total_collateral,
            liquidation_ltv=0.8,
            health_factor=(total_collateral * 0.8) / borrow_amount,
            interest_rate=self._calculate_interest_rate(collateral_assets, borrow_amount),
            interest_type='variable',
            is_active=True
        )

        # Store in data manager
        self.data_manager.collateral_positions.append(position.to_dict())

        return position

    def _calculate_interest_rate(
        self,
        collateral_assets: list[dict[str, Any]],
        borrow_amount: float
    ) -> float:
        """Calculate interest rate based on collateral type and amount."""
        # Base rate
        base_rate = 5.0

        # Adjust based on collateral type
        crypto_percentage = sum(
            asset['value_usd'] for asset in collateral_assets
            if asset['asset_class'] == AssetClass.CRYPTO
        ) / sum(asset['value_usd'] for asset in collateral_assets)

        if crypto_percentage > 0.5:
            # Higher rate for crypto-heavy collateral
            base_rate += 2.0

        # Adjust based on LTV
        ltv = borrow_amount / sum(asset['value_usd'] for asset in collateral_assets)
        if ltv > 0.7:
            base_rate += 1.5
        elif ltv > 0.5:
            base_rate += 0.5

        # Add some randomness
        return base_rate + random.uniform(-0.5, 0.5)

    def get_unified_transaction_history(
        self,
        user_id: int,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get unified transaction history across all systems."""
        transactions = []

        # Traditional transactions
        user_transactions = [
            t for t in self.data_manager.transactions
            if t.get('user_id') == user_id
        ]

        for tx in user_transactions[:limit//3]:
            transactions.append({
                'id': f"fiat_{tx['id']}",
                'type': 'fiat_transaction',
                'amount': tx['amount'],
                'currency': 'USD',
                'description': tx.get('description', 'Transaction'),
                'timestamp': tx.get('transaction_date', tx.get('created_at')),
                'system': 'traditional'
            })

        # Crypto transactions
        crypto_txs = [
            t for t in self.data_manager.crypto_transactions
            if t.get('user_id') == user_id
        ]

        for tx in crypto_txs[:limit//3]:
            transactions.append({
                'id': f"crypto_{tx['id']}",
                'type': 'crypto_transaction',
                'amount': tx['amount'],
                'currency': tx['asset_symbol'],
                'description': f"{tx['direction']} {tx['asset_symbol']}",
                'timestamp': tx.get('created_at'),
                'system': 'crypto'
            })

        # Asset bridges
        user_bridges = [
            b for b in self.data_manager.asset_bridges
            if b.get('user_id') == user_id
        ]

        for bridge in user_bridges[:limit//3]:
            transactions.append({
                'id': f"bridge_{bridge['id']}",
                'type': 'asset_bridge',
                'amount': bridge['from_amount'],
                'currency': bridge['from_asset_name'].split()[-1],
                'description': f"Convert to {bridge['to_asset_name']}",
                'timestamp': bridge.get('initiated_at'),
                'system': 'unified'
            })

        # Sort by timestamp
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)

        return transactions[:limit]

    def generate_conversion_rates(self):
        """Generate and store current conversion rates."""
        # Get all rates from converter
        all_rates = self.asset_converter.get_all_conversion_rates()

        # Store fiat rates
        for from_currency, from_rate in all_rates['fiat'].items():
            for to_currency, to_rate in all_rates['fiat'].items():
                if from_currency != to_currency:
                    rate = ConversionRate(
                        from_asset=from_currency,
                        to_asset=to_currency,
                        rate=to_rate / from_rate,
                        inverse_rate=from_rate / to_rate,
                        source='market',
                        is_active=True
                    )
                    self.data_manager.conversion_rates.append(rate.to_dict())

        # Store crypto-USD rates
        for symbol, price in all_rates['crypto_usd'].items():
            # Crypto to USD
            rate = ConversionRate(
                from_asset=symbol,
                to_asset='USD',
                rate=price,
                inverse_rate=1/price,
                source='market',
                is_active=True
            )
            self.data_manager.conversion_rates.append(rate.to_dict())

    def identify_cross_asset_opportunities(self, user_id: int) -> list[dict[str, Any]]:
        """Identify arbitrage and optimization opportunities."""
        opportunities = []

        # Get user's unified balance
        balance = self.calculate_unified_balance(user_id)

        # Check for high-interest debt that could be refinanced with crypto collateral
        if balance.total_loans > 10000 and balance.total_crypto_usd > balance.total_loans * 2:
            opportunities.append({
                'type': 'refinance',
                'description': 'Refinance high-interest loans with crypto-backed credit',
                'potential_savings': balance.total_loans * 0.05,  # Assume 5% rate reduction
                'risk_level': 'medium',
                'actions': [
                    'Create collateral position with crypto assets',
                    'Pay off existing loans',
                    'Save on interest payments'
                ]
            })

        # Check for idle fiat that could earn yield in DeFi
        if balance.total_fiat_usd > 10000 and balance.defi_positions_value < balance.total_fiat_usd * 0.1:
            opportunities.append({
                'type': 'yield_optimization',
                'description': 'Move idle fiat to stablecoin yield farming',
                'potential_gain': balance.total_fiat_usd * 0.08,  # 8% APY
                'risk_level': 'low',
                'actions': [
                    'Convert fiat to USDC',
                    'Deposit in Aave or Compound',
                    'Earn 6-10% APY'
                ]
            })

        # Check for credit card debt that could use balance transfer
        if balance.credit_utilization > 0.3 and balance.total_credit_available > balance.total_fiat_usd:
            opportunities.append({
                'type': 'balance_transfer',
                'description': 'Transfer high-interest credit card debt',
                'potential_savings': balance.total_credit_available * balance.credit_utilization * 0.15,
                'risk_level': 'low',
                'actions': [
                    'Apply for balance transfer card',
                    'Transfer existing balances',
                    'Pay off during 0% APR period'
                ]
            })

        return opportunities
