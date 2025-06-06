import { jest } from '@jest/globals';
import { currencyConverterService, ConversionType, TradeStatus, OfferType } from '../currencyConverter';
import { fetchApi } from '@/lib/api';

// Mock fetchApi
jest.mock('@/lib/api');
const mockFetchApi = fetchApi as jest.MockedFunction<typeof fetchApi>;

describe('CurrencyConverterService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Currency Management', () => {
    test('getCurrencies fetches all currencies', async () => {
      const mockCurrencies = [
        { code: 'USD', name: 'US Dollar', symbol: '$', is_crypto: false },
        { code: 'EUR', name: 'Euro', symbol: '€', is_crypto: false }
      ];
      mockFetchApi.mockResolvedValueOnce(mockCurrencies);

      const result = await currencyConverterService.getCurrencies();

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/currencies');
      expect(result).toEqual(mockCurrencies);
    });

    test('getCurrency fetches specific currency', async () => {
      const mockCurrency = { code: 'USD', name: 'US Dollar', symbol: '$' };
      mockFetchApi.mockResolvedValueOnce(mockCurrency);

      const result = await currencyConverterService.getCurrency('USD');

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/currencies/USD');
      expect(result).toEqual(mockCurrency);
    });
  });

  describe('Exchange Rates', () => {
    test('getExchangeRates fetches all rates', async () => {
      const mockRates = [
        { from_currency: 'USD', to_currency: 'EUR', rate: 0.92 }
      ];
      mockFetchApi.mockResolvedValueOnce(mockRates);

      const result = await currencyConverterService.getExchangeRates();

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/rates');
      expect(result).toEqual(mockRates);
    });

    test('getExchangeRates with base currency', async () => {
      const mockRates = [
        { from_currency: 'EUR', to_currency: 'USD', rate: 1.09 }
      ];
      mockFetchApi.mockResolvedValueOnce(mockRates);

      const result = await currencyConverterService.getExchangeRates('EUR');

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/rates?base=EUR');
      expect(result).toEqual(mockRates);
    });

    test('getExchangeRate fetches specific rate', async () => {
      const mockRate = { from_currency: 'USD', to_currency: 'EUR', rate: 0.92 };
      mockFetchApi.mockResolvedValueOnce(mockRate);

      const result = await currencyConverterService.getExchangeRate('USD', 'EUR');

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/rates/USD/EUR');
      expect(result).toEqual(mockRate);
    });
  });

  describe('Conversion', () => {
    test('createQuote creates conversion quote', async () => {
      const quoteData = {
        from_currency: 'USD',
        to_currency: 'EUR',
        amount: 1000,
        conversion_type: ConversionType.STANDARD
      };
      const mockQuote = { quote_id: 'Q123', ...quoteData, exchange_rate: 0.92 };
      mockFetchApi.mockResolvedValueOnce(mockQuote);

      const result = await currencyConverterService.createQuote(quoteData);

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/quote', {
        method: 'POST',
        body: JSON.stringify(quoteData)
      });
      expect(result).toEqual(mockQuote);
    });

    test('executeConversion executes from quote', async () => {
      const mockResponse = { transaction_id: 'T123', status: 'completed' };
      mockFetchApi.mockResolvedValueOnce(mockResponse);

      const result = await currencyConverterService.executeConversion('Q123');

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/convert/Q123', {
        method: 'POST'
      });
      expect(result).toEqual(mockResponse);
    });

    test('getConversions fetches conversion history', async () => {
      const mockConversions = [
        { id: 1, from_currency: 'USD', to_currency: 'EUR', amount: 1000 }
      ];
      mockFetchApi.mockResolvedValueOnce(mockConversions);

      const result = await currencyConverterService.getConversions();

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/conversions');
      expect(result).toEqual(mockConversions);
    });
  });

  describe('Balances', () => {
    test('getBalances fetches all balances', async () => {
      const mockBalances = [
        { currency: 'USD', balance: 10000, available_balance: 9500 }
      ];
      mockFetchApi.mockResolvedValueOnce(mockBalances);

      const result = await currencyConverterService.getBalances();

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/balances');
      expect(result).toEqual(mockBalances);
    });

    test('getBalance fetches specific balance', async () => {
      const mockBalance = { currency: 'USD', balance: 10000 };
      mockFetchApi.mockResolvedValueOnce(mockBalance);

      const result = await currencyConverterService.getBalance('USD');

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/balances/USD');
      expect(result).toEqual(mockBalance);
    });
  });

  describe('P2P Trading - Offers', () => {
    test('searchOffers searches without filters', async () => {
      const mockOffers = [
        { id: 1, offer_type: OfferType.SELL, from_currency: 'USD' }
      ];
      mockFetchApi.mockResolvedValueOnce(mockOffers);

      const result = await currencyConverterService.searchOffers();

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/offers');
      expect(result).toEqual(mockOffers);
    });

    test('searchOffers with filters', async () => {
      const mockOffers = [
        { id: 1, offer_type: OfferType.BUY, from_currency: 'EUR' }
      ];
      mockFetchApi.mockResolvedValueOnce(mockOffers);

      const result = await currencyConverterService.searchOffers({
        from_currency: 'EUR',
        to_currency: 'USD',
        offer_type: OfferType.BUY,
        min_amount: 100,
        max_amount: 1000
      });

      expect(mockFetchApi).toHaveBeenCalledWith(
        '/api/currency-converter/p2p/offers?from_currency=EUR&to_currency=USD&offer_type=buy&min_amount=100&max_amount=1000'
      );
      expect(result).toEqual(mockOffers);
    });

    test('createOffer creates new P2P offer', async () => {
      const offerData = {
        offer_type: OfferType.SELL,
        from_currency: 'USD',
        to_currency: 'EUR',
        amount: 1000,
        exchange_rate: 0.92,
        payment_methods: ['bank_transfer']
      };
      const mockOffer = { id: 1, ...offerData, status: 'active' };
      mockFetchApi.mockResolvedValueOnce(mockOffer);

      const result = await currencyConverterService.createOffer(offerData);

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/offers', {
        method: 'POST',
        body: JSON.stringify(offerData)
      });
      expect(result).toEqual(mockOffer);
    });

    test('getOffer fetches specific offer', async () => {
      const mockOffer = { id: 1, offer_type: OfferType.SELL };
      mockFetchApi.mockResolvedValueOnce(mockOffer);

      const result = await currencyConverterService.getOffer(1);

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/offers/1');
      expect(result).toEqual(mockOffer);
    });

    test('cancelOffer cancels offer', async () => {
      mockFetchApi.mockResolvedValueOnce(undefined);

      await currencyConverterService.cancelOffer(1);

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/offers/1', {
        method: 'DELETE'
      });
    });
  });

  describe('P2P Trading - Trades', () => {
    test('createTrade creates new trade', async () => {
      const tradeData = {
        offer_id: 1,
        amount: 500,
        payment_method: 'bank_transfer'
      };
      const mockTrade = { id: 1, ...tradeData, status: TradeStatus.PENDING };
      mockFetchApi.mockResolvedValueOnce(mockTrade);

      const result = await currencyConverterService.createTrade(tradeData);

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/trades', {
        method: 'POST',
        body: JSON.stringify(tradeData)
      });
      expect(result).toEqual(mockTrade);
    });

    test('getTrades fetches all trades', async () => {
      const mockTrades = [
        { id: 1, status: TradeStatus.COMPLETED }
      ];
      mockFetchApi.mockResolvedValueOnce(mockTrades);

      const result = await currencyConverterService.getTrades();

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/trades');
      expect(result).toEqual(mockTrades);
    });

    test('getTrades with status filter', async () => {
      const mockTrades = [
        { id: 1, status: TradeStatus.IN_ESCROW }
      ];
      mockFetchApi.mockResolvedValueOnce(mockTrades);

      const result = await currencyConverterService.getTrades(TradeStatus.IN_ESCROW);

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/trades?status=in_escrow');
      expect(result).toEqual(mockTrades);
    });

    test('confirmPayment confirms trade payment', async () => {
      const mockResponse = { success: true };
      mockFetchApi.mockResolvedValueOnce(mockResponse);

      const result = await currencyConverterService.confirmPayment(1);

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/trades/1/confirm-payment', {
        method: 'PUT'
      });
      expect(result).toEqual(mockResponse);
    });

    test('releaseEscrow releases funds', async () => {
      const mockResponse = { success: true };
      mockFetchApi.mockResolvedValueOnce(mockResponse);

      const result = await currencyConverterService.releaseEscrow(1);

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/trades/1/release-escrow', {
        method: 'PUT'
      });
      expect(result).toEqual(mockResponse);
    });

    test('disputeTrade creates dispute', async () => {
      const mockResponse = { success: true };
      mockFetchApi.mockResolvedValueOnce(mockResponse);

      const result = await currencyConverterService.disputeTrade(1, 'Payment not received');

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/p2p/trades/1/dispute', {
        method: 'PUT',
        body: JSON.stringify({ reason: 'Payment not received' })
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Analytics', () => {
    test('getExchangeStats fetches exchange statistics', async () => {
      const mockStats = {
        total_volume_24h: 1000000,
        total_trades_24h: 500,
        popular_pairs: []
      };
      mockFetchApi.mockResolvedValueOnce(mockStats);

      const result = await currencyConverterService.getExchangeStats();

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/stats');
      expect(result).toEqual(mockStats);
    });

    test('getUserStats fetches user statistics', async () => {
      const mockStats = {
        total_conversions: 50,
        total_volume: 50000,
        p2p_trades_completed: 10,
        p2p_rating: 4.8
      };
      mockFetchApi.mockResolvedValueOnce(mockStats);

      const result = await currencyConverterService.getUserStats();

      expect(mockFetchApi).toHaveBeenCalledWith('/api/currency-converter/user-stats');
      expect(result).toEqual(mockStats);
    });
  });

  describe('Error Handling', () => {
    test('handles API errors gracefully', async () => {
      const error = new Error('API Error');
      mockFetchApi.mockRejectedValueOnce(error);

      await expect(currencyConverterService.getCurrencies()).rejects.toThrow('API Error');
    });
  });
});