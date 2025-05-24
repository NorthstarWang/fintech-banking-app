import { apiClient } from './client';

// Enums
export enum TradeStatus {
  OPEN = 'open',
  IN_ESCROW = 'in_escrow',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  DISPUTED = 'disputed'
}

export enum OfferStatus {
  ACTIVE = 'active',
  MATCHED = 'matched',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled'
}

export enum PaymentMethod {
  BANK_TRANSFER = 'bank_transfer',
  CREDIT_CARD = 'credit_card',
  DEBIT_CARD = 'debit_card',
  PAYPAL = 'paypal',
  CRYPTO = 'crypto',
  CASH = 'cash'
}

// Interfaces
export interface Currency {
  code: string;
  name: string;
  symbol: string;
  country: string;
  is_crypto: boolean;
  is_supported: boolean;
  decimal_places: number;
  icon_url?: string;
}

export interface ExchangeRate {
  from_currency: string;
  to_currency: string;
  rate: number;
  bid: number;
  ask: number;
  spread_percentage: number;
  last_updated: string;
  provider: string;
}

export interface PeerOffer {
  id: number;
  user_id: number;
  offer_type: 'buy' | 'sell';
  from_currency: string;
  to_currency: string;
  amount: number;
  exchange_rate: number;
  min_amount: number;
  max_amount: number;
  payment_methods: PaymentMethod[];
  status: OfferStatus;
  expires_at: string;
  created_at: string;
  user?: {
    id: number;
    username: string;
    rating: number;
    completed_trades: number;
    verified: boolean;
  };
}

export interface P2PTrade {
  id: number;
  offer_id: number;
  buyer_id: number;
  seller_id: number;
  amount: number;
  exchange_rate: number;
  from_currency: string;
  to_currency: string;
  from_amount: number;
  to_amount: number;
  payment_method: PaymentMethod;
  status: TradeStatus;
  escrow_released: boolean;
  created_at: string;
  completed_at?: string;
  offer?: PeerOffer;
  buyer?: {
    id: number;
    username: string;
    rating: number;
  };
  seller?: {
    id: number;
    username: string;
    rating: number;
  };
}

export interface UserBalance {
  currency: string;
  available_balance: number;
  locked_balance: number;
  total_balance: number;
  last_updated: string;
}

export interface ConversionQuote {
  from_currency: string;
  to_currency: string;
  from_amount: number;
  to_amount: number;
  exchange_rate: number;
  fee_amount: number;
  fee_percentage: number;
  total_amount: number;
  expires_at: string;
  quote_id: string;
}

// Request types
export interface ConversionRequest {
  from_currency: string;
  to_currency: string;
  amount: number;
  conversion_type?: 'standard' | 'p2p';
}

export interface CreateOfferRequest {
  offer_type: 'buy' | 'sell';
  from_currency: string;
  to_currency: string;
  amount: number;
  exchange_rate: number;
  min_amount?: number;
  max_amount?: number;
  payment_methods: PaymentMethod[];
  expires_in_hours?: number;
}

export interface CreateTradeRequest {
  offer_id: number;
  amount: number;
  payment_method: PaymentMethod;
}

export interface P2PSearchParams {
  from_currency?: string;
  to_currency?: string;
  offer_type?: 'buy' | 'sell';
  min_amount?: number;
  max_amount?: number;
  payment_method?: PaymentMethod;
  min_rating?: number;
  verified_only?: boolean;
}

// Service class
class CurrencyConverterService {
  // Currencies
  async getSupportedCurrencies(): Promise<Currency[]> {
    return apiClient.get<Currency[]>('/api/currency-converter/currencies');
  }

  async getCurrency(code: string): Promise<Currency> {
    return apiClient.get<Currency>(`/api/currency-converter/currencies/${code}`);
  }

  // Exchange Rates
  async getExchangeRates(baseCurrency?: string): Promise<ExchangeRate[]> {
    const params = baseCurrency ? `?base=${baseCurrency}` : '';
    return apiClient.get<ExchangeRate[]>(`/api/currency-converter/rates${params}`);
  }

  async getExchangeRate(fromCurrency: string, toCurrency: string): Promise<ExchangeRate> {
    return apiClient.get<ExchangeRate>(`/api/currency-converter/rates/${fromCurrency}/${toCurrency}`);
  }

  // Conversions
  async getConversionQuote(data: ConversionRequest): Promise<ConversionQuote> {
    return apiClient.post<ConversionQuote>('/api/currency-converter/quote', data);
  }

  async executeConversion(quoteId: string): Promise<{
    transaction_id: string;
    status: 'completed' | 'pending' | 'failed';
    from_amount: number;
    to_amount: number;
    exchange_rate: number;
    fee_amount: number;
    completed_at?: string;
  }> {
    return apiClient.post(`/api/currency-converter/convert/${quoteId}`, {});
  }

  async getConversionHistory(limit?: number): Promise<Array<{
    id: string;
    from_currency: string;
    to_currency: string;
    from_amount: number;
    to_amount: number;
    exchange_rate: number;
    fee_amount: number;
    status: string;
    created_at: string;
  }>> {
    const params = limit ? `?limit=${limit}` : '';
    return apiClient.get(`/api/currency-converter/conversions${params}`);
  }

  // User Balances
  async getBalances(): Promise<UserBalance[]> {
    return apiClient.get<UserBalance[]>('/api/currency-converter/balances');
  }

  async getBalance(currency: string): Promise<UserBalance> {
    return apiClient.get<UserBalance>(`/api/currency-converter/balances/${currency}`);
  }

  // P2P Trading
  async searchOffers(params?: P2PSearchParams): Promise<PeerOffer[]> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get<PeerOffer[]>(`/api/currency-converter/p2p/offers?${queryParams.toString()}`);
  }

  async createOffer(data: CreateOfferRequest): Promise<PeerOffer> {
    return apiClient.post<PeerOffer>('/api/currency-converter/p2p/offers', data);
  }

  async getOffer(offerId: number): Promise<PeerOffer> {
    return apiClient.get<PeerOffer>(`/api/currency-converter/p2p/offers/${offerId}`);
  }

  async cancelOffer(offerId: number): Promise<void> {
    return apiClient.delete<void>(`/api/currency-converter/p2p/offers/${offerId}`);
  }

  async createTrade(data: CreateTradeRequest): Promise<P2PTrade> {
    return apiClient.post<P2PTrade>('/api/currency-converter/p2p/trades', data);
  }

  async getTrades(status?: TradeStatus): Promise<P2PTrade[]> {
    const params = status ? `?status=${status}` : '';
    return apiClient.get<P2PTrade[]>(`/api/currency-converter/p2p/trades${params}`);
  }

  async getTrade(tradeId: number): Promise<P2PTrade> {
    return apiClient.get<P2PTrade>(`/api/currency-converter/p2p/trades/${tradeId}`);
  }

  async confirmPayment(tradeId: number): Promise<P2PTrade> {
    return apiClient.put<P2PTrade>(`/api/currency-converter/p2p/trades/${tradeId}/confirm-payment`, {});
  }

  async releaseEscrow(tradeId: number): Promise<P2PTrade> {
    return apiClient.put<P2PTrade>(`/api/currency-converter/p2p/trades/${tradeId}/release-escrow`, {});
  }

  async disputeTrade(tradeId: number, reason: string): Promise<P2PTrade> {
    return apiClient.put<P2PTrade>(`/api/currency-converter/p2p/trades/${tradeId}/dispute`, { reason });
  }

  // Analytics
  async getExchangeStats(): Promise<{
    total_volume_24h: number;
    total_trades_24h: number;
    popular_pairs: Array<{
      from_currency: string;
      to_currency: string;
      volume: number;
      trade_count: number;
    }>;
    average_rates: { [key: string]: number };
  }> {
    return apiClient.get('/api/currency-converter/stats');
  }

  async getUserStats(): Promise<{
    total_conversions: number;
    total_volume: number;
    p2p_trades_completed: number;
    p2p_rating: number;
    favorite_currencies: string[];
  }> {
    return apiClient.get('/api/currency-converter/user-stats');
  }
}

// Export singleton instance
export const currencyConverterService = new CurrencyConverterService();