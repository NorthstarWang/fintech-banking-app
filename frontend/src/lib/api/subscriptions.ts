import { apiClient } from './client';

export interface Subscription {
  id: number;
  user_id: number;
  name: string;
  merchant_name: string;
  category: 'STREAMING' | 'SOFTWARE' | 'FITNESS' | 'FOOD' | 'NEWS' | 'UTILITIES' | 'GAMING' | 'EDUCATION' | 'OTHER';
  status: 'ACTIVE' | 'PAUSED' | 'CANCELLED' | 'EXPIRED' | 'TRIAL';
  amount: number;
  billing_cycle: 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'YEARLY' | 'CUSTOM';
  next_billing_date: string;
  last_billing_date?: string;
  start_date: string;
  end_date?: string;
  free_trial_end_date?: string;
  transaction_ids: number[];
  detected_automatically: boolean;
  confidence_score?: number;
  created_at: string;
  updated_at: string;
  is_trial?: boolean;
  regular_price?: number;
  days_until_billing?: number;
}

export interface SubscriptionCreate {
  name: string;
  merchant_name: string;
  category: Subscription['category'];
  amount: number;
  billing_cycle: Subscription['billing_cycle'];
  next_billing_date: string;
  start_date?: string;
  free_trial_end_date?: string;
}

export interface SubscriptionUpdate {
  name?: string;
  category?: Subscription['category'];
  status?: Subscription['status'];
  amount?: number;
  billing_cycle?: Subscription['billing_cycle'];
  next_billing_date?: string;
  notes?: string;
}

export interface SubscriptionAnalysis {
  total_subscriptions: number;
  active_subscriptions: number;
  total_monthly_cost: number;
  total_annual_cost: number;
  cost_by_category: Record<string, number>;
  cost_trend: Array<{ date: string; amount: number }>;
  most_expensive: Array<{ id: number; name: string; amount: number }>;
  least_used: Array<{ id: number; name: string; last_used?: string }>;
  upcoming_renewals: Array<{ id: number; name: string; date: string; amount: number }>;
  savings_opportunities: number;
  average_subscription_cost: number;
}

export interface CancellationReminder {
  id: number;
  subscription_id: number;
  user_id: number;
  reminder_date: string;
  reason?: string;
  is_sent: boolean;
  created_at: string;
}

export interface OptimizationSuggestion {
  subscription_id: number;
  subscription_name: string;
  suggestion_type: 'DOWNGRADE' | 'BUNDLE' | 'CANCEL_UNUSED' | 'ANNUAL_DISCOUNT' | 'ALTERNATIVE_SERVICE' | 'NEGOTIATE_PRICE';
  current_cost: number;
  potential_savings: number;
  alternative_name?: string;
  alternative_cost?: number;
  reason: string;
  confidence: number;
  action_steps: string[];
}

export interface OptimizationResponse {
  total_potential_savings: number;
  suggestions: OptimizationSuggestion[];
  bundling_opportunities: Array<Record<string, any>>;
  unused_subscriptions: Array<Record<string, any>>;
  duplicate_services: Array<Record<string, any>>;
}

class SubscriptionsService {
  async getSubscriptions(filters?: { status?: string; category?: string }): Promise<Subscription[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.category) params.append('category', filters.category);
    
    return apiClient.get<Subscription[]>(`/api/subscriptions?${params.toString()}`);
  }

  async getSubscription(id: number): Promise<Subscription> {
    return apiClient.get<Subscription>(`/api/subscriptions/${id}`);
  }

  async createSubscription(data: SubscriptionCreate): Promise<Subscription> {
    return apiClient.post<Subscription>('/api/subscriptions', data);
  }

  async updateSubscription(id: number, data: SubscriptionUpdate): Promise<Subscription> {
    return apiClient.put<Subscription>(`/api/subscriptions/${id}`, data);
  }

  async deleteSubscription(id: number): Promise<void> {
    return apiClient.delete<void>(`/api/subscriptions/${id}`);
  }

  async getSubscriptionAnalysis(): Promise<SubscriptionAnalysis> {
    return apiClient.get<SubscriptionAnalysis>('/api/subscriptions/analysis');
  }

  async createCancellationReminder(subscriptionId: number, data: {
    days_before: number;
    reason?: string;
    target_date?: string;
  }): Promise<CancellationReminder> {
    return apiClient.post<CancellationReminder>(
      `/api/subscriptions/${subscriptionId}/reminders`,
      data
    );
  }

  async getOptimizationSuggestions(): Promise<OptimizationResponse> {
    return apiClient.get<OptimizationResponse>('/api/subscriptions/optimize');
  }

  async pauseSubscription(id: number): Promise<Subscription> {
    return apiClient.post<Subscription>(`/api/subscriptions/${id}/pause`);
  }

  async resumeSubscription(id: number): Promise<Subscription> {
    return apiClient.post<Subscription>(`/api/subscriptions/${id}/resume`);
  }

  async detectSubscriptions(): Promise<{ detected: number; subscriptions: Subscription[] }> {
    return apiClient.post<{ detected: number; subscriptions: Subscription[] }>(
      '/api/subscriptions/detect'
    );
  }
}

// Export singleton instance
export const subscriptionsService = new SubscriptionsService();