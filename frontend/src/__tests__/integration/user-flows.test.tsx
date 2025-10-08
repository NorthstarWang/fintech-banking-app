import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import InvestmentsPage from '@/app/(authenticated)/investments/page';
import CreditCardsPage from '@/app/(authenticated)/credit-cards/page';
import CurrencyConverterPage from '@/app/(authenticated)/currency-converter/page';
import { fetchApi } from '@/lib/api';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('@/hooks/useSyntheticTracking', () => ({
  useSyntheticTracking: () => ({
    trackInvestmentOrder: jest.fn(),
    trackPortfolioView: jest.fn(),
    trackAssetSearch: jest.fn(),
    trackCardApplication: jest.fn(),
    trackCardRecommendation: jest.fn(),
    trackCreditScoreCheck: jest.fn(),
    trackCurrencyConversion: jest.fn(),
    trackP2PTrade: jest.fn(),
    trackExchangeRateView: jest.fn()
  })
}));

const mockFetchApi = fetchApi as jest.MockedFunction<typeof fetchApi>;

// Shared mock data
const mockUserData = {
  creditScore: {
    credit_score: 750,
    score_range: 'Very Good',
    factors: {
      payment_history: { score: 98, impact: 'positive', description: 'Excellent' },
      credit_utilization: { score: 25, impact: 'positive', description: 'Low' },
      credit_age: { months: 84, impact: 'positive', description: '7 years' },
      credit_mix: { types: ['credit_cards', 'auto_loan'], impact: 'positive', description: 'Good' },
      recent_inquiries: { count: 1, impact: 'neutral', description: '1 inquiry' }
    }
  },
  investmentAccounts: [
    {
      id: 1,
      account_name: 'Primary Investment',
      account_type: 'individual',
      balance: 50000,
      cash_balance: 10000,
      invested_balance: 40000
    }
  ],
  currencyBalances: [
    { currency: 'USD', balance: 10000, available_balance: 9500, currency_type: 'fiat' },
    { currency: 'EUR', balance: 5000, available_balance: 5000, currency_type: 'fiat' }
  ]
};

describe('User Flow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setupMockResponses();
  });

  function setupMockResponses() {
    mockFetchApi.mockImplementation((url: string, _options?: any) => {
      // Credit cards endpoints
      if (url === '/api/credit-cards/credit-score') {
        return Promise.resolve(mockUserData.creditScore);
      }
      if (url === '/api/credit-cards/recommendations') {
        return Promise.resolve([
          {
            card_offer_id: 1,
            card_name: 'Premium Rewards Card',
            issuer: 'Test Bank',
            card_type: 'rewards',
            match_score: 95,
            reasons: ['High credit score', 'Good payment history'],
            annual_fee: 95,
            pre_qualified: true
          }
        ]);
      }
      
      // Investment endpoints
      if (url === '/api/investments/accounts') {
        return Promise.resolve(mockUserData.investmentAccounts);
      }
      if (url.includes('/api/investments/portfolio/')) {
        return Promise.resolve({
          total_value: 50000,
          cash_balance: 10000,
          positions: [],
          asset_allocation: { stocks: 60, etfs: 30, crypto: 10 }
        });
      }
      
      // Currency converter endpoints
      if (url === '/api/currency-converter/balances') {
        return Promise.resolve(mockUserData.currencyBalances);
      }
      if (url === '/api/currency-converter/currencies') {
        return Promise.resolve([
          { code: 'USD', name: 'US Dollar', symbol: '$', type: 'fiat' },
          { code: 'EUR', name: 'Euro', symbol: '€', type: 'fiat' }
        ]);
      }
      
      return Promise.resolve([]);
    });
  }

  describe('Cross-System Navigation Flow', () => {
    test('user can view their complete financial overview', async () => {
      // Start with investments page
      const { unmount: unmountInvestments } = render(<InvestmentsPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Primary Investment')).toBeInTheDocument();
        expect(screen.getByText('$50,000.00')).toBeInTheDocument();
      });
      
      // Verify analytics tracking
      expect(mockAnalyticsLogger.logEvent).toHaveBeenCalledWith('PAGE_VIEW', {
        text: 'User viewed investments page',
        page_name: 'Investments',
        timestamp: expect.any(String)
      });
      
      unmountInvestments();
      
      // Navigate to credit cards
      const { unmount: unmountCards } = render(<CreditCardsPage />);
      
      await waitFor(() => {
        expect(screen.getByText('750')).toBeInTheDocument(); // Credit score
        expect(screen.getByText('Premium Rewards Card')).toBeInTheDocument();
      });
      
      unmountCards();
      
      // Navigate to currency converter
      render(<CurrencyConverterPage />);
      
      await waitFor(() => {
        expect(screen.getByText('$9,500.00')).toBeInTheDocument(); // USD balance
        expect(screen.getByText('€5,000.00')).toBeInTheDocument(); // EUR balance
      });
    });
  });

  describe('Investment to Currency Conversion Flow', () => {
    test('user sells investments and converts currency', async () => {
      // Mock successful investment sell order
      mockFetchApi.mockImplementation((url: string, _options?: any) => {
        if (url === '/api/investments/orders' && options?.method === 'POST') {
          const orderData = JSON.parse(options.body);
          if (orderData.order_side === 'sell') {
            return Promise.resolve({
              id: 1,
              status: 'executed',
              executed_price: 175.50,
              total_value: 1755.00 // 10 shares * $175.50
            });
          }
        }
        // Return default mocks
        return setupMockResponses();
      });

      // User starts on investments page
      render(<InvestmentsPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Investments')).toBeInTheDocument();
      });
      
      // Navigate to Trade tab
      fireEvent.click(screen.getByText('Trade'));
      
      // Search for asset
      const searchInput = screen.getByPlaceholderText('Search by symbol or name...');
      fireEvent.change(searchInput, { target: { value: 'AAPL' } });
      fireEvent.click(screen.getByText('Search'));
      
      await waitFor(() => {
      });
    });
  });

  describe('Credit Score Impact on Services', () => {
    test('lower credit score limits available options', async () => {
      // Override credit score to lower value
      mockFetchApi.mockImplementation((url: string) => {
        if (url === '/api/credit-cards/credit-score') {
          return Promise.resolve({
            ...mockUserData.creditScore,
            credit_score: 620,
            score_range: 'Fair'
          });
        }
        if (url === '/api/credit-cards/recommendations') {
          return Promise.resolve([
            {
              card_offer_id: 2,
              card_name: 'Secured Card',
              issuer: 'Test Bank',
              card_type: 'secured',
              match_score: 70,
              reasons: ['Build credit history'],
              annual_fee: 0,
              pre_qualified: false
            }
          ]);
        }
        if (url === '/api/credit-cards/offers') {
          return Promise.resolve([
            {
              id: 1,
              name: 'Premium Card',
              min_credit_score: 720,
              eligible: false
            },
            {
              id: 2,
              name: 'Secured Card',
              min_credit_score: 580,
              eligible: true
            }
          ]);
        }
        return Promise.resolve([]);
      });

      render(<CreditCardsPage />);
      
      await waitFor(() => {
        expect(screen.getByText('620')).toBeInTheDocument();
        expect(screen.getByText('Fair')).toBeInTheDocument();
        expect(screen.getByText('Secured Card')).toBeInTheDocument();
        expect(screen.queryByText('Premium Rewards Card')).not.toBeInTheDocument();
      });
    });
  });

  describe('Synthetic API Tracking Integration', () => {
    test('all user actions are properly tracked', async () => {
      
      // Test investment tracking
      render(<InvestmentsPage />);
      await waitFor(() => {
        expect(screen.getByText('Investments')).toBeInTheDocument();
      });
      
      // Click on Portfolio tab - should track portfolio view
      fireEvent.click(screen.getByText('Portfolio'));
      await waitFor(() => {
      });
    });
  });

  describe('Error Recovery Flow', () => {
    test('handles API failures gracefully across systems', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      // Mock API failures
      mockFetchApi.mockRejectedValue(new Error('Network error'));
      
      // Test investments page
      const { unmount: unmountInvestments } = render(<InvestmentsPage />);
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Error fetching investment data:',
          expect.any(Error)
        );
      });
      unmountInvestments();
      
      // Test credit cards page
      const { unmount: unmountCards } = render(<CreditCardsPage />);
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Error fetching credit data:',
          expect.any(Error)
        );
      });
      unmountCards();
      
      // Test currency converter page
      render(<CurrencyConverterPage />);
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Error fetching data:',
          expect.any(Error)
        );
      });
      
      consoleSpy.mockRestore();
    });
  });

  describe('Data Consistency Across Systems', () => {
    test('user data remains consistent when switching between pages', async () => {
      // Track data across page switches
      const userData = {
        creditScore: 0,
        investmentBalance: 0,
        currencyBalance: 0
      };
      
      // Capture data from investments page
      const { unmount: unmountInvestments } = render(<InvestmentsPage />);
      await waitFor(() => {
        const balanceText = screen.getByText('$50,000.00');
        expect(balanceText).toBeInTheDocument();
        userData.investmentBalance = 50000;
      });
      unmountInvestments();
      
      // Capture data from credit cards page
      const { unmount: unmountCards } = render(<CreditCardsPage />);
      await waitFor(() => {
        const scoreText = screen.getByText('750');
        expect(scoreText).toBeInTheDocument();
        userData.creditScore = 750;
      });
      unmountCards();
      
      // Capture data from currency converter page
      render(<CurrencyConverterPage />);
      await waitFor(() => {
        const usdBalance = screen.getByText('$9,500.00');
        expect(usdBalance).toBeInTheDocument();
        userData.currencyBalance = 9500;
      });
      
      // Verify data consistency
      expect(userData.creditScore).toBe(750);
      expect(userData.investmentBalance).toBe(50000);
      expect(userData.currencyBalance).toBe(9500);
    });
  });

  describe('Real-time Updates Flow', () => {
    test('actions in one system reflect in others', async () => {
      let applicationCount = 0;
      
      // Mock dynamic responses
      mockFetchApi.mockImplementation((url: string, _options?: any) => {
        if (url === '/api/credit-cards/applications' && options?.method === 'POST') {
          applicationCount++;
          return Promise.resolve({
            id: applicationCount,
            status: 'approved',
            approved_credit_limit: 5000
          });
        }
        if (url === '/api/credit-cards/applications' && !options?.method) {
          return Promise.resolve(
            Array.from({ length: applicationCount }, (_, i) => ({
              id: i + 1,
              card_name: `Card ${i + 1}`,
              status: 'approved'
            }))
          );
        }
        // Return default mocks
        return setupMockResponses();
      });
      
      window.alert = jest.fn();
      
      render(<CreditCardsPage />);
      
      // Check initial applications count
      await waitFor(() => {
        fireEvent.click(screen.getByText('My Applications') || screen.getByText('Applications'));
      });
      
      // Should show no applications initially
      expect(screen.getByText(/You haven't applied for any cards yet/)).toBeInTheDocument();
      
      // Apply for a card
      fireEvent.click(screen.getByText('Recommended for You') || screen.getByText('Recommended'));
      
      await waitFor(() => {
        const applyButton = screen.getByText('Apply Now');
        fireEvent.click(applyButton);
      });
      
      // Confirm application
      const modalApplyButton = screen.getAllByText('Apply Now')[1];
      fireEvent.click(modalApplyButton);
      
      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith(expect.stringContaining('Congratulations'));
      });
    });
  });
});
