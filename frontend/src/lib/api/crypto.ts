import { apiClient } from './client';
import { CryptoWallet, CryptoAsset, NFTAsset, CryptoTransaction, DeFiPosition, AssetBridge } from '@/types';

// Wallet Management
export const cryptoApi = {
  // Get all crypto wallets for user
  async getWallets() {
    return apiClient<CryptoWallet[]>('/api/crypto/wallets');
  },

  // Get specific wallet details
  async getWallet(walletId: string) {
    return apiClient<CryptoWallet>(`/api/crypto/wallets/${walletId}`);
  },

  // Create new wallet
  async createWallet(data: {
    name: string;
    network: string;
    type: string;
  }) {
    return apiClient<CryptoWallet>('/api/crypto/wallets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Update wallet
  async updateWallet(walletId: string, data: Partial<CryptoWallet>) {
    return apiClient<CryptoWallet>(`/api/crypto/wallets/${walletId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Delete wallet
  async deleteWallet(walletId: string) {
    return apiClient<{ message: string }>(`/api/crypto/wallets/${walletId}`, {
      method: 'DELETE',
    });
  },

  // Get crypto assets
  async getAssets(walletId?: string) {
    const params = walletId ? `?wallet_id=${walletId}` : '';
    return apiClient<CryptoAsset[]>(`/api/crypto/assets${params}`);
  },

  // Get NFT assets
  async getNFTs(walletId?: string) {
    const params = walletId ? `?wallet_id=${walletId}` : '';
    return apiClient<NFTAsset[]>(`/api/crypto/nfts${params}`);
  },

  // Get crypto transactions
  async getTransactions(walletId?: string, assetId?: string) {
    const params = new URLSearchParams();
    if (walletId) params.append('wallet_id', walletId);
    if (assetId) params.append('asset_id', assetId);
    return apiClient<CryptoTransaction[]>(`/api/crypto/transactions?${params.toString()}`);
  },

  // Execute crypto transaction
  async executeTransaction(data: {
    fromWalletId: string;
    toAddress: string;
    assetId: string;
    amount: number;
    network: string;
    type: 'send' | 'receive' | 'swap' | 'stake' | 'unstake';
  }) {
    return apiClient<CryptoTransaction>('/api/crypto/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Get DeFi positions
  async getDeFiPositions(walletId?: string) {
    const params = walletId ? `?wallet_id=${walletId}` : '';
    return apiClient<DeFiPosition[]>(`/api/crypto/defi${params}`);
  },

  // Create DeFi position
  async createDeFiPosition(data: {
    walletId: string;
    protocol: string;
    positionType: string;
    assetId: string;
    amount: number;
    apy: number;
  }) {
    return apiClient<DeFiPosition>('/api/crypto/defi', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Close DeFi position
  async closeDeFiPosition(positionId: string) {
    return apiClient<{ message: string; transaction: CryptoTransaction }>(`/api/crypto/defi/${positionId}/close`, {
      method: 'POST',
    });
  },

  // Get asset bridges (for conversion)
  async getAssetBridges() {
    return apiClient<AssetBridge[]>('/api/crypto/bridges');
  },

  // Convert between assets
  async convertAsset(data: {
    fromAssetId: string;
    toAssetId: string;
    amount: number;
    fromWalletId: string;
    toWalletId?: string;
  }) {
    return apiClient<{
      transaction: CryptoTransaction;
      exchangeRate: number;
      fees: number;
    }>('/api/crypto/convert', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Get market prices
  async getMarketPrices(assetIds?: string[]) {
    const params = assetIds ? `?assets=${assetIds.join(',')}` : '';
    return apiClient<Record<string, {
      usd: number;
      change24h: number;
      marketCap: number;
    }>>(`/api/crypto/prices${params}`);
  },

  // Get portfolio summary
  async getPortfolioSummary() {
    return apiClient<{
      totalValueUSD: number;
      totalValueBTC: number;
      change24h: number;
      change7d: number;
      topAssets: Array<{
        asset: CryptoAsset;
        valueUSD: number;
        percentage: number;
      }>;
      assetAllocation: Array<{
        assetType: string;
        valueUSD: number;
        percentage: number;
      }>;
    }>('/api/crypto/portfolio/summary');
  },

  // Get staking opportunities
  async getStakingOpportunities() {
    return apiClient<Array<{
      assetId: string;
      assetSymbol: string;
      apy: number;
      minimumStake: number;
      lockPeriod: number;
      protocol: string;
    }>>('/api/crypto/staking/opportunities');
  },

  // Estimate gas fees
  async estimateGasFees(network: string, transactionType: string) {
    return apiClient<{
      slow: number;
      standard: number;
      fast: number;
      currency: string;
    }>(`/api/crypto/gas-fees/${network}?type=${transactionType}`);
  }
};