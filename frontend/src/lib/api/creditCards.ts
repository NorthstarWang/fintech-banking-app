import { apiClient } from './client';

// Enums
export enum CardCategory {
  CASH_BACK = 'cash_back',
  TRAVEL = 'travel',
  REWARDS = 'rewards',
  BUSINESS = 'business',
  STUDENT = 'student',
  SECURED = 'secured',
  BALANCE_TRANSFER = 'balance_transfer'
}

export enum ApplicationStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  WITHDRAWN = 'withdrawn'
}

export enum EmploymentType {
  FULL_TIME = 'full_time',
  PART_TIME = 'part_time',
  SELF_EMPLOYED = 'self_employed',
  STUDENT = 'student',
  RETIRED = 'retired',
  UNEMPLOYED = 'unemployed'
}

// Interfaces
export interface CreditCard {
  id: number;
  card_name: string;
  issuer: string;
  category: CardCategory;
  annual_fee: number;
  apr_min: number;
  apr_max: number;
  intro_apr?: number;
  intro_apr_period?: number;
  cashback_rate?: number;
  rewards_rate?: number;
  signup_bonus?: string;
  signup_bonus_requirement?: string;
  benefits: string[];
  fees: { [key: string]: number };
  credit_score_required: number;
  image_url?: string;
  apply_url?: string;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

export interface CardApplication {
  id: number;
  user_id: number;
  card_id: number;
  status: ApplicationStatus;
  annual_income: number;
  employment_type: EmploymentType;
  employment_duration_months: number;
  housing_payment: number;
  existing_cards_count: number;
  requested_credit_limit?: number;
  application_date: string;
  decision_date?: string;
  rejection_reasons?: string[];
  approved_credit_limit?: number;
  card?: CreditCard;
}

export interface CreditScoreInfo {
  score: number;
  rating: 'poor' | 'fair' | 'good' | 'very_good' | 'excellent';
  factors: string[];
  last_updated: string;
}

export interface CardRecommendation {
  card: CreditCard;
  match_score: number;
  reasons: string[];
  estimated_approval_odds: 'low' | 'medium' | 'high';
  estimated_credit_limit?: number;
}

// Request types
export interface CardApplicationRequest {
  card_id: number;
  annual_income: number;
  employment_type: EmploymentType;
  employment_duration_months: number;
  housing_payment: number;
  existing_cards_count: number;
  requested_credit_limit?: number;
}

export interface CardSearchParams {
  category?: CardCategory;
  min_credit_score?: number;
  max_annual_fee?: number;
  has_intro_apr?: boolean;
  has_signup_bonus?: boolean;
  limit?: number;
}

export interface RecommendationParams {
  income_level?: 'low' | 'medium' | 'high';
  spending_categories?: string[];
  preferred_benefits?: string[];
  limit?: number;
}

// Service class
class CreditCardsService {
  // Credit Cards
  async getCards(params?: CardSearchParams): Promise<CreditCard[]> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get<CreditCard[]>(`/api/credit-cards?${queryParams.toString()}`);
  }

  async getCard(cardId: number): Promise<CreditCard> {
    return apiClient.get<CreditCard>(`/api/credit-cards/${cardId}`);
  }

  async getFeaturedCards(): Promise<CreditCard[]> {
    return apiClient.get<CreditCard[]>('/api/credit-cards/featured');
  }

  // Credit Score
  async getCreditScore(): Promise<CreditScoreInfo> {
    return apiClient.get<CreditScoreInfo>('/api/credit-cards/credit-score');
  }

  async updateCreditScore(score: number): Promise<CreditScoreInfo> {
    return apiClient.put<CreditScoreInfo>('/api/credit-cards/credit-score', { score });
  }

  // Recommendations
  async getRecommendations(params?: RecommendationParams): Promise<CardRecommendation[]> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          if (Array.isArray(value)) {
            queryParams.append(key, value.join(','));
          } else {
            queryParams.append(key, value.toString());
          }
        }
      });
    }
    return apiClient.get<CardRecommendation[]>(`/api/credit-cards/recommendations?${queryParams.toString()}`);
  }

  async getPersonalizedRecommendations(): Promise<CardRecommendation[]> {
    return apiClient.get<CardRecommendation[]>('/api/credit-cards/recommendations/personalized');
  }

  // Applications
  async getApplications(): Promise<CardApplication[]> {
    return apiClient.get<CardApplication[]>('/api/credit-cards/applications');
  }

  async getApplication(applicationId: number): Promise<CardApplication> {
    return apiClient.get<CardApplication>(`/api/credit-cards/applications/${applicationId}`);
  }

  async submitApplication(data: CardApplicationRequest): Promise<CardApplication> {
    return apiClient.post<CardApplication>('/api/credit-cards/applications', data);
  }

  async withdrawApplication(applicationId: number): Promise<CardApplication> {
    return apiClient.put<CardApplication>(`/api/credit-cards/applications/${applicationId}/withdraw`, {});
  }

  // Card Comparison
  async compareCards(cardIds: number[]): Promise<{
    cards: CreditCard[];
    comparison_matrix: {
      feature: string;
      values: (string | number | boolean)[];
    }[];
  }> {
    return apiClient.post('/api/credit-cards/compare', { card_ids: cardIds });
  }

  // Eligibility Check
  async checkEligibility(cardId: number): Promise<{
    eligible: boolean;
    approval_odds: 'low' | 'medium' | 'high';
    reasons: string[];
    recommendations?: string[];
  }> {
    return apiClient.post(`/api/credit-cards/${cardId}/check-eligibility`, {});
  }

  // Analytics
  async getApplicationStats(): Promise<{
    total_applications: number;
    approved_count: number;
    rejected_count: number;
    pending_count: number;
    approval_rate: number;
    average_credit_limit: number;
    popular_categories: { category: CardCategory; count: number }[];
  }> {
    return apiClient.get('/api/credit-cards/applications/stats');
  }
}

// Export singleton instance
export const creditCardsService = new CreditCardsService();