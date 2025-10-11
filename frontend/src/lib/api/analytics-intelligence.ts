import { apiClient } from './client';

// Enhanced analytics types
export interface TransactionVelocity {
  transactions_per_day: number;
  transactions_per_week: number;
  transactions_per_month: number;
  average_transaction_size: number;
  total_transactions: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface CashFlow {
  period_days: number;
  money_in: number;
  money_out: number;
  net_flow: number;
  savings_rate: number;
  categories: Array<{
    category: string;
    type: 'income' | 'expense';
    amount: number;
  }>;
}

export interface InvestmentPerformance {
  total_value: number;
  total_cost_basis: number;
  total_gain_loss: number;
  total_gain_loss_percentage: number;
  asset_allocation: Array<{
    asset_type: string;
    value: number;
    percentage: number;
  }>;
  top_performers: Array<{
    symbol: string;
    asset_type: string;
    current_value: number;
    gain_loss: number;
    gain_loss_percentage: number;
  }>;
  worst_performers: Array<{
    symbol: string;
    asset_type: string;
    current_value: number;
    gain_loss: number;
    gain_loss_percentage: number;
  }>;
}

export interface Anomaly {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  transaction_id?: number;
  amount?: number;
  description: string;
  detected_at: string;
}

export interface SubscriptionInsights {
  total_monthly_cost: number;
  total_annual_cost: number;
  subscription_count: number;
  active_subscriptions: number;
  recommendations: Array<{
    subscription_id: number;
    service_name: string;
    type: string;
    suggestion: string;
  }>;
}

export interface LoanRisk {
  total_outstanding: number;
  monthly_payment_total: number;
  risk_score: number;
  risk_level: 'none' | 'low' | 'medium' | 'high' | 'critical';
  risk_factors: string[];
  loans: Array<{
    loan_id: number;
    loan_type: string;
    principal_remaining: number;
    monthly_payment: number;
    next_payment_date: string | null;
    risk_score: number;
  }>;
}

export interface BudgetAdherence {
  total_budgets: number;
  on_track_count: number;
  over_budget_count: number;
  at_risk_count: number;
  budgets: Array<{
    budget_id: number;
    category_name: string;
    budgeted_amount: number;
    spent_amount: number;
    percentage_used: number;
    projected_spend: number;
    projected_percentage: number;
    status: 'on_track' | 'at_risk' | 'over_budget';
    period: string;
    period_start: string;
    period_end: string;
  }>;
}

export interface SpendingTrends {
  period_months: number;
  total_categories: number;
  trends: Array<{
    category: string;
    average_monthly: number;
    standard_deviation: number;
    trend_direction: 'increasing' | 'decreasing' | 'stable';
    change_percentage: number;
    monthly_breakdown: Record<string, number>;
  }>;
}

export interface FinancialHealth {
  overall_score: number;
  rating: 'Excellent' | 'Good' | 'Fair' | 'Needs Improvement';
  factors: Array<{
    factor: string;
    score: number;
    max_score: number;
    value: string;
  }>;
  recommendations: string[];
}

export interface DashboardSummary {
  summary: {
    net_worth: number;
    total_assets: number;
    total_liabilities: number;
    monthly_cash_flow: number;
    savings_rate: number;
    financial_health_score: number;
    financial_health_rating: string;
  };
  cash_flow: CashFlow;
  investment_performance: InvestmentPerformance;
  budget_adherence: {
    total_budgets: number;
    on_track_count: number;
    over_budget_count: number;
    at_risk_count: number;
  };
  anomalies: {
    count: number;
    recent: Anomaly[];
  };
  timestamp: string;
}

class AnalyticsIntelligenceService {
  async getTransactionVelocity(days = 30): Promise<TransactionVelocity> {
    return apiClient.get<TransactionVelocity>(
      `/api/analytics/intelligence/transaction-velocity?days=${days}`
    );
  }

  async getCashFlow(periodDays = 30): Promise<CashFlow> {
    return apiClient.get<CashFlow>(
      `/api/analytics/intelligence/cash-flow?period_days=${periodDays}`
    );
  }

  async getInvestmentPerformance(): Promise<InvestmentPerformance> {
    return apiClient.get<InvestmentPerformance>(
      '/api/analytics/intelligence/investment-performance'
    );
  }

  async detectAnomalies(lookbackDays = 90): Promise<{ anomalies: Anomaly[]; count: number; lookback_days: number }> {
    return apiClient.get(
      `/api/analytics/intelligence/anomalies?lookback_days=${lookbackDays}`
    );
  }

  async getSubscriptionInsights(): Promise<SubscriptionInsights> {
    return apiClient.get<SubscriptionInsights>(
      '/api/analytics/intelligence/subscription-insights'
    );
  }

  async getLoanRisk(): Promise<LoanRisk> {
    return apiClient.get<LoanRisk>(
      '/api/analytics/intelligence/loan-risk'
    );
  }

  async getBudgetAdherence(): Promise<BudgetAdherence> {
    return apiClient.get<BudgetAdherence>(
      '/api/analytics/intelligence/budget-adherence'
    );
  }

  async getSpendingTrends(months = 6): Promise<SpendingTrends> {
    return apiClient.get<SpendingTrends>(
      `/api/analytics/intelligence/spending-trends?months=${months}`
    );
  }

  async getFinancialHealth(): Promise<FinancialHealth> {
    return apiClient.get<FinancialHealth>(
      '/api/analytics/intelligence/financial-health'
    );
  }

  async getDashboardSummary(): Promise<DashboardSummary> {
    return apiClient.get<DashboardSummary>(
      '/api/analytics/intelligence/dashboard-summary'
    );
  }

  // WebSocket connection for real-time updates
  connectWebSocket(onMessage: (data: unknown) => void, onError?: (error: Event) => void): WebSocket | null {
    const token = apiClient.getAuthToken();
    if (!token) {
      console.error('No auth token available for WebSocket connection');
      return null;
    }

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/api/analytics/ws/analytics?token=${token}`);

    ws.onopen = () => {
      // WebSocket connected
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      if (onError) {
        onError(event);
      }
    };

    ws.onclose = () => {
      // WebSocket disconnected
    };

    return ws;
  }
}

export const analyticsIntelligenceService = new AnalyticsIntelligenceService();
