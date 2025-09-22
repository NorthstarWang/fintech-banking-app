// Crypto Types
export interface CryptoWallet {
  id: string;
  userId: number;
  name: string;
  address: string;
  network: string;
  type: 'hot' | 'cold' | 'exchange';
  balance: number;
  balanceUSD: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CryptoAsset {
  id: string;
  walletId: string;
  symbol: string;
  name: string;
  assetType: 'native' | 'token' | 'stablecoin';
  contractAddress?: string;
  balance: number;
  balanceUSD: number;
  price: number;
  change24h: number;
  icon?: string;
}

export interface NFTAsset {
  id: string;
  walletId: string;
  contractAddress: string;
  tokenId: string;
  name: string;
  description?: string;
  imageUrl?: string;
  collection: string;
  rarity?: string;
  floorPrice?: number;
  estimatedValue?: number;
  attributes: Record<string, any>;
}

export interface CryptoTransaction {
  id: string;
  walletId: string;
  type: 'send' | 'receive' | 'swap' | 'stake' | 'unstake' | 'mint' | 'burn';
  assetId: string;
  amount: number;
  amountUSD: number;
  fromAddress: string;
  toAddress: string;
  txHash: string;
  status: 'pending' | 'confirmed' | 'failed';
  network: string;
  gasFee: number;
  gasFeeUSD: number;
  timestamp: string;
  blockNumber?: number;
  confirmations?: number;
}

export interface DeFiPosition {
  id: string;
  walletId: string;
  protocol: string;
  protocolIcon?: string;
  positionType: 'lending' | 'borrowing' | 'liquidity' | 'staking' | 'farming';
  assetId: string;
  amount: number;
  valueUSD: number;
  apy: number;
  rewards?: {
    tokenSymbol: string;
    amount: number;
    valueUSD: number;
  }[];
  startDate: string;
  maturityDate?: string;
  isActive: boolean;
}

export interface AssetBridge {
  id: string;
  fromAsset: string;
  toAsset: string;
  fromNetwork: string;
  toNetwork: string;
  exchangeRate: number;
  fee: number;
  minAmount: number;
  maxAmount: number;
  estimatedTime: number;
}

// Loan Types
export interface Loan {
  id: string;
  userId: number;
  loanType: 'personal' | 'auto' | 'mortgage' | 'student' | 'business' | 'crypto_backed';
  status: 'active' | 'paid_off' | 'defaulted' | 'refinanced';
  principal: number;
  balance: number;
  interestRate: number;
  term: number;
  monthlyPayment: number;
  startDate: string;
  endDate: string;
  nextPaymentDate: string;
  lender: string;
  collateral?: {
    type: string;
    value: number;
    description: string;
  };
  refinanceEligible: boolean;
  earlyPayoffPenalty: number;
}

export interface LoanApplication {
  id: string;
  userId: number;
  loanType: string;
  status: 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'withdrawn';
  requestedAmount: number;
  proposedTerm: number;
  purpose: string;
  employmentInfo?: {
    employer: string;
    position: string;
    income: number;
    employmentLength: number;
  };
  creditScore?: number;
  debtToIncome?: number;
  submittedAt?: string;
  reviewedAt?: string;
  decision?: {
    approved: boolean;
    reason?: string;
    conditions?: string[];
  };
}

export interface LoanOffer {
  id: string;
  applicationId: string;
  lender: string;
  lenderLogo?: string;
  amount: number;
  interestRate: number;
  apr: number;
  term: number;
  monthlyPayment: number;
  totalInterest: number;
  fees: {
    origination: number;
    processing: number;
    other: number;
  };
  features: string[];
  expiresAt: string;
  isPreApproved: boolean;
}

export interface LoanPaymentSchedule {
  paymentNumber: number;
  dueDate: string;
  payment: number;
  principal: number;
  interest: number;
  balance: number;
  status: 'scheduled' | 'paid' | 'late' | 'missed';
  paidDate?: string;
  paidAmount?: number;
}

// Insurance Types
export interface InsurancePolicy {
  id: string;
  userId: number;
  policyNumber: string;
  policyType: 'health' | 'auto' | 'home' | 'life' | 'disability' | 'travel' | 'pet' | 'dental' | 'vision';
  status: 'active' | 'lapsed' | 'cancelled' | 'expired';
  provider: string;
  providerLogo?: string;
  premium: number;
  premiumFrequency: 'monthly' | 'quarterly' | 'semi-annual' | 'annual';
  deductible: number;
  coverageAmount: number;
  startDate: string;
  endDate: string;
  renewalDate: string;
  beneficiaries?: Array<{
    name: string;
    relationship: string;
    percentage: number;
  }>;
  coverage: Record<string, any>;
  documents: string[];
  autoRenew: boolean;
}

export interface InsuranceClaim {
  id: string;
  policyId: string;
  claimNumber: string;
  status: 'draft' | 'submitted' | 'under_review' | 'approved' | 'denied' | 'paid' | 'closed';
  claimType: string;
  description: string;
  dateOfIncident: string;
  filedDate: string;
  claimAmount: number;
  approvedAmount?: number;
  paidAmount?: number;
  deductibleApplied?: number;
  adjuster?: {
    name: string;
    contact: string;
  };
  documents: Array<{
    id: string;
    name: string;
    type: string;
    uploadDate: string;
  }>;
  timeline: Array<{
    date: string;
    event: string;
    description: string;
  }>;
  paymentInfo?: {
    method: string;
    date: string;
    reference: string;
  };
}

export interface InsuranceProvider {
  id: string;
  name: string;
  logo?: string;
  types: string[];
  rating: number;
  reviewCount: number;
  features: string[];
  contact: {
    phone: string;
    email: string;
    website: string;
  };
  networkSize?: string;
  claimSatisfaction?: number;
  avgProcessingTime?: string;
}

// Unified/Connection Layer Types (for future use)
export interface UnifiedBalance {
  id: string;
  userId: number;
  assetClass: 'fiat' | 'crypto' | 'nft' | 'credit' | 'investment';
  assetType: string;
  assetName: string;
  balance: number;
  balanceUSD: number;
  source: string;
  sourceId: string;
  lastUpdated: string;
}

export interface CollateralPosition {
  id: string;
  userId: number;
  assetId: string;
  assetType: string;
  lockedAmount: number;
  lockedValueUSD: number;
  purpose: string;
  purposeId: string;
  unlockDate?: string;
  ltv?: number;
  liquidationPrice?: number;
}