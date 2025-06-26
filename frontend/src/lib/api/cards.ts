import { apiClient } from './client';

export interface Card {
  id: number;
  user_id: number;
  account_id: number;
  card_name: string;
  card_type: 'credit' | 'debit' | 'virtual';
  card_number?: string;
  cvv?: string;
  last_four: string;
  issuer?: string;
  is_active: boolean;
  status?: string;
  linked_account_id?: number;
  credit_limit?: number;
  current_balance?: number;
  available_credit?: number;
  billing_cycle_day?: number;
  interest_rate?: number;
  expiry_date?: string;
  rewards_program?: string;
  rewards_rate?: number;
  rewards_points?: number;
  rewards_cashback?: number;
  created_at: string;
  updated_at?: string;
  spending_limit?: number;
  spent_amount?: number;
  single_use?: boolean;
  merchant_restrictions?: string[];
  is_contactless_enabled?: boolean;
  is_international_enabled?: boolean;
  is_online_enabled?: boolean;
  is_atm_enabled?: boolean;
  is_default?: boolean;
  due_date?: string;
  minimum_payment?: number;
  last_payment?: { amount: number; date: string };
}

export interface VirtualCard {
  id: number;
  account_id: number;
  card_number_masked: string;
  card_type: 'VIRTUAL' | 'PHYSICAL';
  status: 'ACTIVE' | 'FROZEN' | 'EXPIRED' | 'CANCELLED';
  spending_limit?: number;
  spent_amount: number;
  merchant_restrictions?: string[];
  single_use: boolean;
  name?: string;
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
  is_virtual?: boolean;
  parent_card_id?: number;
}

export interface CardCreate {
  card_number: string;
  card_type: 'credit' | 'debit';
  card_name: string;
  issuer?: string;
  linked_account_id?: number;
  credit_limit?: number;
  current_balance?: number;
  billing_cycle_day?: number;
  interest_rate?: number;
  expiry_date?: string;
  rewards_program?: string;
  rewards_rate?: number;
}

export interface CardUpdate {
  card_name?: string;
  credit_limit?: number;
  is_active?: boolean;
  billing_cycle_day?: number;
  interest_rate?: number;
}

export interface VirtualCardCreate {
  account_id: number;
  spending_limit?: number;
  merchant_restrictions?: string[];
  expires_in_days?: number;
  single_use?: boolean;
  name?: string;
}

export interface SpendingLimitRequest {
  daily_limit?: number;
  monthly_limit?: number;
  category_limits?: Record<string, number>;
}

export interface SpendingLimitResponse {
  card_id: number;
  daily_limit?: number;
  daily_usage: number;
  monthly_limit?: number;
  monthly_usage: number;
  category_limits?: Record<string, { limit: number; usage: number }>;
  limits: Array<{
    id: number;
    limit_amount: number;
    limit_period: string;
    current_usage: number;
    remaining: number;
    merchant_categories?: string[];
    period_start: string;
    period_end: string;
  }>;
}

export interface CardAnalytics {
  total_credit_limit: number;
  total_balance: number;
  utilization_rate: number;
  cards_by_type: {
    credit: number;
    debit: number;
    virtual: number;
  };
  spending_by_category: Record<string, number>;
  average_transaction_size: number;
  total_cards: number;
  active_cards: number;
}

export interface CardDetailedAnalytics {
  card_id: number;
  total_transactions: number;
  total_spent: number;
  average_transaction: number;
  top_merchants: Array<{ merchant: string; amount: number }>;
  spending_by_category: Record<string, number>;
  daily_spending_trend: Array<{ date: string; amount: number }>;
  fraud_alerts: number;
  period_start: string;
  period_end: string;
}

export interface CardStatement {
  statement_period: string;
  previous_balance: number;
  payments: number;
  purchases: number;
  interest_charged: number;
  new_balance: number;
  minimum_payment: number;
  due_date: string;
  transactions: Array<{
    date: string;
    description: string;
    amount: number;
    type: string;
  }>;
}

export interface CardRewards {
  total_rewards: number;
  pending_rewards: number;
  available_rewards: number;
  rewards_history: Array<{
    date: string;
    description: string;
    amount: number;
    rewards_earned: number;
    rate: string;
  }>;
}

export interface CardPaymentRequest {
  amount: number;
  from_account_id: number;
  payment_date: string;
}

export interface AlertConfig {
  payment_due_alert?: boolean;
  high_balance_alert?: boolean;
  high_balance_threshold?: number;
  unusual_activity_alert?: boolean;
}

export interface FraudReport {
  transaction_ids: number[];
  description: string;
  contact_number: string;
}

// Standard Card Operations
export const cardsApi = {
  // List all cards
  async getCards(params?: { card_type?: string; is_active?: boolean }) {
    const queryParams = new URLSearchParams();
    if (params?.card_type) queryParams.append('card_type', params.card_type);
    if (params?.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
    return apiClient.get<Card[]>(`/api/cards${queryParams.toString() ? `?${queryParams.toString()}` : ''}`);
  },

  // Get card by ID
  async getCard(cardId: number) {
    return apiClient.get<Card>(`/api/cards/${cardId}`);
  },

  // Create new card
  async createCard(data: CardCreate) {
    return apiClient.post<Card>('/api/cards', data);
  },

  // Update card
  async updateCard(cardId: number, data: CardUpdate) {
    return apiClient.put<Card>(`/api/cards/${cardId}`, data);
  },

  // Deactivate card
  async deactivateCard(cardId: number) {
    return apiClient.post<{ id: number; is_active: boolean; message: string }>(
      `/api/cards/${cardId}/deactivate`
    );
  },

  // Get card transactions
  async getCardTransactions(cardId: number, limit = 100, offset = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    return apiClient.get<Array<{
      id: number;
      amount: number;
      description: string;
      transaction_date: string;
      merchant: string;
      category: string;
      status: string;
    }>>(`/api/cards/${cardId}/transactions?${params.toString()}`);
  },

  // Get card statement
  async getCardStatement(cardId: number, year: number, month: number) {
    return apiClient.get<CardStatement>(`/api/cards/${cardId}/statement/${year}/${month}`);
  },

  // Make card payment
  async makeCardPayment(cardId: number, data: CardPaymentRequest) {
    return apiClient.post<{
      payment_id: number;
      amount: number;
      new_balance: number;
      payment_date: string;
    }>(`/api/cards/${cardId}/payment`, data);
  },

  // Get card rewards
  async getCardRewards(cardId: number) {
    return apiClient.get<CardRewards>(`/api/cards/${cardId}/rewards`);
  },

  // Get overall analytics
  async getAnalytics() {
    return apiClient.get<CardAnalytics>('/api/cards/analytics');
  },

  // Get card-specific analytics
  async getCardAnalytics(cardId: number, days = 30) {
    const params = new URLSearchParams({ days: days.toString() });
    return apiClient.get<CardDetailedAnalytics>(`/api/cards/${cardId}/analytics?${params.toString()}`);
  },

  // Spending Limits
  async getSpendingLimits(cardId: number) {
    return apiClient.get<SpendingLimitResponse>(`/api/cards/${cardId}/spending-limit`);
  },

  async setSpendingLimits(cardId: number, data: SpendingLimitRequest) {
    return apiClient.put<{
      card_id: number;
      daily_limit?: number;
      monthly_limit?: number;
      category_limits?: Record<string, number>;
      updated_at: string;
    }>(`/api/cards/${cardId}/spending-limit`, data);
  },

  // Alerts
  async configureAlerts(cardId: number, config: AlertConfig) {
    return apiClient.put<{
      card_id: number;
      payment_due_alert?: boolean;
      high_balance_alert?: boolean;
      high_balance_threshold?: number;
      unusual_activity_alert?: boolean;
      updated_at: string;
    }>(`/api/cards/${cardId}/alerts`, config);
  },

  // Fraud Report
  async reportFraud(cardId: number, report: FraudReport) {
    return apiClient.post<{
      case_number: string;
      card_blocked: boolean;
      new_card_ordered: boolean;
      estimated_delivery: string;
    }>(`/api/cards/${cardId}/fraud-report`, report);
  },

  // Virtual Cards
  async createVirtualCard(data: VirtualCardCreate) {
    return apiClient.post<VirtualCard>('/api/cards/virtual', data);
  },

  async createVirtualCardFromParent(parentCardId: number, data: VirtualCardCreate) {
    return apiClient.post<VirtualCard>(`/api/cards/${parentCardId}/virtual`, data);
  },

  async getVirtualCards(params?: { account_id?: number; include_expired?: boolean }) {
    const queryParams = new URLSearchParams();
    if (params?.account_id) queryParams.append('account_id', params.account_id.toString());
    if (params?.include_expired !== undefined) queryParams.append('include_expired', params.include_expired.toString());
    return apiClient.get<VirtualCard[]>(`/api/cards/virtual${queryParams.toString() ? `?${queryParams.toString()}` : ''}`);
  },

  async freezeCard(cardId: number, freeze: boolean, reason?: string) {
    return apiClient.put<VirtualCard>(`/api/cards/${cardId}/freeze`, { freeze, reason });
  },

  async setCardLimit(cardId: number, data: {
    limit_amount: number;
    limit_period: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'PER_TRANSACTION';
    merchant_categories?: string[];
  }) {
    return apiClient.post<{
      id: number;
      card_id: number;
      limit_amount: number;
      limit_period: string;
      merchant_categories?: string[];
      current_usage: number;
      created_at: string;
      is_active: boolean;
    }>(`/api/cards/${cardId}/limits`, data);
  }
};

export default cardsApi;