from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Crypto-specific enums
class CryptoAssetType(str, Enum):
    NATIVE = "native"  # ETH, BTC, etc
    TOKEN = "token"    # ERC-20, etc
    STABLECOIN = "stablecoin"  # USDC, USDT
    NFT = "nft"

class BlockchainNetwork(str, Enum):
    ETHEREUM = "ethereum"
    BITCOIN = "bitcoin"
    POLYGON = "polygon"
    SOLANA = "solana"
    ARBITRUM = "arbitrum"

class TransactionDirection(str, Enum):
    SEND = "send"
    RECEIVE = "receive"
    SWAP = "swap"
    MINT = "mint"
    BURN = "burn"

class DeFiProtocolType(str, Enum):
    LENDING = "lending"
    STAKING = "staking"
    LIQUIDITY = "liquidity"
    YIELD_FARMING = "yield_farming"

# Request/Response Models
class CryptoWalletCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    network: BlockchainNetwork
    is_primary: bool = False
    
class CryptoWalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: str
    address: str
    network: BlockchainNetwork
    is_primary: bool
    created_at: datetime
    last_synced: Optional[datetime] = None

class CryptoAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    wallet_id: int
    symbol: str
    name: str
    asset_type: CryptoAssetType
    network: BlockchainNetwork
    contract_address: Optional[str] = None
    balance: str  # Using string for precision
    usd_value: float
    price_usd: float
    change_24h: float
    last_updated: datetime

class NFTAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    wallet_id: int
    collection_name: str
    token_id: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Dict[str, Any]
    network: BlockchainNetwork
    contract_address: str
    floor_price_usd: Optional[float] = None
    estimated_value_usd: Optional[float] = None
    acquired_at: datetime
    last_updated: datetime

class CryptoTransactionCreate(BaseModel):
    from_wallet_id: Optional[int] = None
    to_address: str
    asset_symbol: str
    amount: str
    network: BlockchainNetwork
    gas_price_gwei: Optional[float] = None
    note: Optional[str] = None

class CryptoTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    wallet_id: Optional[int] = None
    direction: TransactionDirection
    asset_symbol: str
    amount: str
    usd_value_at_time: float
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    network: BlockchainNetwork
    transaction_hash: str
    gas_fee: Optional[str] = None
    gas_fee_usd: Optional[float] = None
    status: str  # pending, confirmed, failed
    confirmations: int
    note: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None

class DeFiPositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    wallet_id: int
    protocol: str
    protocol_type: DeFiProtocolType
    position_type: str  # lending, borrowing, staking, LP
    asset_symbol: str
    amount: str
    usd_value: float
    apy: float
    rewards_earned: str
    rewards_usd: float
    started_at: datetime
    last_updated: datetime

class CryptoPortfolioSummary(BaseModel):
    total_usd_value: float
    total_assets: int
    total_nfts: int
    chains: List[str]
    top_holdings: List[Dict[str, Any]]
    defi_positions_value: float
    total_24h_change: float
    total_24h_change_percent: float

class CryptoSwapRequest(BaseModel):
    from_asset: str
    to_asset: str
    amount: str
    slippage_tolerance: float = 0.5  # percentage
    wallet_id: int

class CryptoSwapQuote(BaseModel):
    from_asset: str
    to_asset: str
    from_amount: str
    to_amount: str
    price_impact: float
    gas_estimate_usd: float
    route: List[str]
    expires_at: datetime