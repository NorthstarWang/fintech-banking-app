import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import InvestmentsPage from '../page';
import { apiClient } from '@/lib/api/client';

// Mock dependencies
jest.mock('@/lib/api/client');
jest.mock('@/hooks/useSyntheticTracking', () => ({
  useSyntheticTracking: () => ({
    trackInvestmentOrder: jest.fn(),
    trackPortfolioView: jest.fn(),
    trackAssetSearch: jest.fn()
  })
}));

// Mock analytics logger
const mockAnalyticsLogger = {
  logEvent: jest.fn(),
  logPageView: jest.fn(),
  logUserAction: jest.fn()
};

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('InvestmentsPage', () => {
  const mockAccounts = [
    {
      id: 1,
      account_name: 'Test Investment Account',
      account_type: 'individual',
      account_number: 'INV123456',
      balance: 50000,
      cash_balance: 10000,
      invested_balance: 40000,
      total_return: 5000,
      total_return_percentage: 12.5,
      daily_change: 250,
      daily_change_percentage: 0.5
    }
  ];

  const mockAssets = [
    {
      id: 1,
      symbol: 'AAPL',
      name: 'Apple Inc.',
      asset_type: 'stock',
      current_price: 175.50,
      price_change: 2.50,
      price_change_percentage: 1.44,
      market_cap: 2800000000000,
      volume: 50000000
    },
    {
      id: 2,
      symbol: 'VOO',
      name: 'Vanguard S&P 500 ETF',
      asset_type: 'etf',
      current_price: 425.30,
      price_change: -1.20,
      price_change_percentage: -0.28,
      expense_ratio: 0.03
    }
  ];

  const mockPortfolio = {
    total_value: 50000,
    cash_balance: 10000,
    invested_balance: 40000,
    total_return: 5000,
    total_return_percentage: 12.5,
    daily_change: 250,
    daily_change_percentage: 0.5,
    positions: [
      {
        asset_id: 1,
        symbol: 'AAPL',
        name: 'Apple Inc.',
        quantity: 100,
        average_cost: 150.00,
        current_price: 175.50,
        current_value: 17550,
        total_return: 2550,
        total_return_percentage: 17.0
      }
    ],
    asset_allocation: {
      stocks: 70,
      etfs: 20,
      crypto: 10
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Manually set up mock functions
    mockApiClient.get = jest.fn();
    mockApiClient.post = jest.fn();
    mockApiClient.put = jest.fn();
    mockApiClient.delete = jest.fn();
    mockApiClient.setAuthToken = jest.fn();
    mockApiClient.getAuthToken = jest.fn();

    mockApiClient.get.mockImplementation((url: string) => {
      if (url === '/api/investments/accounts') {
        return Promise.resolve(mockAccounts);
      }
      if (url === '/api/investments/assets/featured') {
        return Promise.resolve(mockAssets);
      }
      if (url.includes('/api/investments/portfolio/')) {
        return Promise.resolve(mockPortfolio);
      }
      if (url.includes('/api/investments/assets/search')) {
        return Promise.resolve(mockAssets);
      }
      return Promise.resolve([]);
    });
  });

  test('renders investment page and loads data', async () => {
    render(<InvestmentsPage />);

    // Check page title
    expect(screen.getByText('Investments')).toBeInTheDocument();
    expect(screen.getByText('Manage your investment portfolio')).toBeInTheDocument();

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Test Investment Account')).toBeInTheDocument();
      expect(screen.getByText('$50,000.00')).toBeInTheDocument();
    });

    // Verify analytics tracking
    expect(mockAnalyticsLogger.logEvent).toHaveBeenCalledWith('PAGE_VIEW', {
      text: 'User viewed investments page',
      page_name: 'Investments',
      timestamp: expect.any(String)
    });
  });

  test('displays account information correctly', async () => {
    render(<InvestmentsPage />);

    await waitFor(() => {
      const accountCard = screen.getByText('Test Investment Account').closest('div');
      expect(accountCard).toBeInTheDocument();
      expect(screen.getByText('Individual')).toBeInTheDocument();
      expect(screen.getByText('$10,000.00')).toBeInTheDocument(); // Cash balance
      expect(screen.getByText('+12.50%')).toBeInTheDocument(); // Total return percentage
    });
  });

  test('tab navigation works correctly', async () => {
    render(<InvestmentsPage />);

    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });

    // Click on Portfolio tab
    fireEvent.click(screen.getByText('Portfolio'));
    expect(screen.getByText('Portfolio Performance')).toBeInTheDocument();

    // Click on Trade tab
    fireEvent.click(screen.getByText('Trade'));
    expect(screen.getByText('Search Assets')).toBeInTheDocument();

    // Click on Watchlist tab
    fireEvent.click(screen.getByText('Watchlist'));
    expect(screen.getByText('Create New Watchlist')).toBeInTheDocument();
  });

  test('asset search functionality', async () => {
    render(<InvestmentsPage />);

    // Navigate to Trade tab
    await waitFor(() => {
      fireEvent.click(screen.getByText('Trade'));
    });

    // Type in search input
    const searchInput = screen.getByPlaceholderText('Search by symbol or name...');
    fireEvent.change(searchInput, { target: { value: 'AAPL' } });

    // Click search button
    fireEvent.click(screen.getByText('Search'));

    await waitFor(() => {
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
      expect(screen.getByText('$175.50')).toBeInTheDocument();
    });
  });

  test('place order modal opens and closes', async () => {
    render(<InvestmentsPage />);

    // Navigate to Trade tab
    await waitFor(() => {
      fireEvent.click(screen.getByText('Trade'));
    });

    // Search for assets
    const searchInput = screen.getByPlaceholderText('Search by symbol or name...');
    fireEvent.change(searchInput, { target: { value: 'AAPL' } });
    fireEvent.click(screen.getByText('Search'));

    // Wait for results and click Buy button
    await waitFor(() => {
      const buyButton = screen.getAllByText('Buy')[0];
      fireEvent.click(buyButton);
    });

    // Check modal is open
    expect(screen.getByText('Place Order - AAPL')).toBeInTheDocument();
    expect(screen.getByText('Apple Inc.')).toBeInTheDocument();

    // Close modal
    fireEvent.click(screen.getByText('Cancel'));
    await waitFor(() => {
      expect(screen.queryByText('Place Order - AAPL')).not.toBeInTheDocument();
    });
  });

  test('portfolio allocation chart renders', async () => {
    render(<InvestmentsPage />);

    // Navigate to Portfolio tab
    await waitFor(() => {
      fireEvent.click(screen.getByText('Portfolio'));
    });

    // Check for allocation data
    await waitFor(() => {
      expect(screen.getByText('Asset Allocation')).toBeInTheDocument();
      expect(screen.getByText('Stocks')).toBeInTheDocument();
      expect(screen.getByText('70%')).toBeInTheDocument();
      expect(screen.getByText('ETFs')).toBeInTheDocument();
      expect(screen.getByText('20%')).toBeInTheDocument();
    });
  });

  test('error handling when API fails', async () => {
    mockApiClient.get.mockRejectedValueOnce(new Error('API Error'));
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    render(<InvestmentsPage />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error fetching investment data:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });
});
