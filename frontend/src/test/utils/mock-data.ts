// Mock data generators for testing

export const mockAccount = (overrides = {}) => ({
  id: 1,
  account_number: '1234567890',
  account_name: 'Test Checking',
  account_type: 'checking',
  balance: 1000.00,
  currency: 'USD',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

export const mockTransaction = (overrides = {}) => ({
  id: 1,
  account_id: 1,
  amount: 50.00,
  transaction_type: 'DEBIT',
  description: 'Test Transaction',
  merchant: 'Test Merchant',
  category_id: 1,
  transaction_date: '2024-01-01T00:00:00Z',
  status: 'completed',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

export const mockNotification = (overrides = {}) => ({
  id: 1,
  title: 'Test Notification',
  message: 'This is a test notification',
  type: 'info',
  created_at: '2024-01-01T00:00:00Z',
  is_read: false,
  user_id: 1,
  ...overrides,
})

export const mockCard = (overrides = {}) => ({
  id: 1,
  card_number: '**** **** **** 1234',
  card_type: 'credit',
  card_name: 'Test Card',
  credit_limit: 5000.00,
  current_balance: 1000.00,
  available_credit: 4000.00,
  interest_rate: 19.99,
  minimum_payment: 25.00,
  payment_due_date: '2024-02-01',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

export const mockBudget = (overrides = {}) => ({
  id: 1,
  category_id: 1,
  budget_amount: 500.00,
  period: 'monthly',
  start_date: '2024-01-01',
  end_date: '2024-01-31',
  current_spending: 250.00,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

export const mockGoal = (overrides = {}) => ({
  id: 1,
  name: 'Emergency Fund',
  target_amount: 10000.00,
  current_amount: 5000.00,
  target_date: '2024-12-31',
  category: 'savings',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})