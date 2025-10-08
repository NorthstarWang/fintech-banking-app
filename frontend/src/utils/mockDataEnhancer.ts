// Enhanced mock data generator for demo scenarios
export interface EnhancedTransaction {
  id: string;
  description: string;
  amount: number;
  type: 'credit' | 'debit';
  category: string;
  date: string;
  status: 'completed' | 'pending';
  merchant: string;
  location?: string;
  recurring?: boolean;
  tags?: string[];
}

export interface DemoNotification {
  id: string;
  type: 'info' | 'warning' | 'success' | 'alert';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
  actionLabel?: string;
}

export interface DemoGoal {
  id: string;
  name: string;
  targetAmount: number;
  currentAmount: number;
  deadline: string;
  category: 'vacation' | 'emergency' | 'purchase' | 'investment' | 'other';
  color: string;
  milestones: {
    percentage: number;
    reached: boolean;
    reachedDate?: string;
  }[];
}

// Realistic spending patterns
const _SPENDING_PATTERNS = {
  morning: ['coffee', 'breakfast', 'gas', 'parking'],
  lunch: ['restaurant', 'fast-food', 'grocery'],
  evening: ['dinner', 'entertainment', 'shopping'],
  weekend: ['shopping', 'entertainment', 'dining', 'activities'],
  recurring: ['subscription', 'utility', 'insurance', 'rent', 'loan'],
};

const MERCHANT_POOLS = {
  coffee: ['Starbucks', 'Peet\'s Coffee', 'Blue Bottle', 'Local Coffee Shop'],
  restaurant: ['Chipotle', 'Sweetgreen', 'Local Bistro', 'Olive Garden'],
  grocery: ['Whole Foods', 'Trader Joe\'s', 'Safeway', 'Target'],
  gas: ['Shell', 'Chevron', 'BP', 'Exxon'],
  entertainment: ['Netflix', 'AMC Theaters', 'Spotify', 'Local Cinema'],
  shopping: ['Amazon', 'Target', 'Best Buy', 'Walmart', 'Nordstrom'],
  utility: ['PG&E', 'Water Company', 'Internet Provider', 'Phone Bill'],
};

// Generate realistic transaction patterns
export function generateRealisticTransactions(
  days: number = 30,
  accountBalance: number = 5000
): EnhancedTransaction[] {
  const transactions: EnhancedTransaction[] = [];
  const today = new Date();
  let _runningBalance = accountBalance;

  for (let day = 0; day < days; day++) {
    const currentDate = new Date(today);
    currentDate.setDate(currentDate.getDate() - day);
    const dayOfWeek = currentDate.getDay();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    
    // Morning transactions (weekdays mostly)
    if (!isWeekend && Math.random() > 0.3) {
      const coffeeAmount = 4.50 + Math.random() * 3;
      transactions.push({
        id: `trans-${transactions.length + 1}`,
        description: 'Morning Coffee',
        amount: coffeeAmount,
        type: 'debit',
        category: 'Dining',
        date: new Date(currentDate.setHours(8, Math.floor(Math.random() * 30))).toISOString(),
        status: 'completed',
        merchant: MERCHANT_POOLS.coffee[Math.floor(Math.random() * MERCHANT_POOLS.coffee.length)],
        location: 'Downtown',
        tags: ['coffee', 'morning-routine'],
      });
      _runningBalance -= coffeeAmount;
    }

    // Lunch transactions
    if (Math.random() > 0.4) {
      const lunchAmount = 12 + Math.random() * 15;
      transactions.push({
        id: `trans-${transactions.length + 1}`,
        description: 'Lunch',
        amount: lunchAmount,
        type: 'debit',
        category: 'Dining',
        date: new Date(currentDate.setHours(12, Math.floor(Math.random() * 60))).toISOString(),
        status: 'completed',
        merchant: MERCHANT_POOLS.restaurant[Math.floor(Math.random() * MERCHANT_POOLS.restaurant.length)],
        tags: ['lunch', 'food'],
      });
      _runningBalance -= lunchAmount;
    }

    // Random shopping (more likely on weekends)
    if ((isWeekend && Math.random() > 0.3) || Math.random() > 0.8) {
      const shoppingAmount = 25 + Math.random() * 150;
      transactions.push({
        id: `trans-${transactions.length + 1}`,
        description: 'Shopping',
        amount: shoppingAmount,
        type: 'debit',
        category: 'Shopping',
        date: new Date(currentDate.setHours(14 + Math.floor(Math.random() * 6))).toISOString(),
        status: 'completed',
        merchant: MERCHANT_POOLS.shopping[Math.floor(Math.random() * MERCHANT_POOLS.shopping.length)],
        tags: isWeekend ? ['weekend-shopping'] : ['shopping'],
      });
      _runningBalance -= shoppingAmount;
    }

    // Salary/income (twice a month)
    if (day === 15 || day === 0) {
      transactions.push({
        id: `trans-${transactions.length + 1}`,
        description: 'Salary Deposit',
        amount: 2500,
        type: 'credit',
        category: 'Income',
        date: new Date(currentDate.setHours(9, 0)).toISOString(),
        status: 'completed',
        merchant: 'Employer Inc.',
        tags: ['salary', 'income'],
      });
      _runningBalance += 2500;
    }

    // Recurring bills (specific days)
    if (day === 1) {
      // Rent
      transactions.push({
        id: `trans-${transactions.length + 1}`,
        description: 'Monthly Rent',
        amount: 1500,
        type: 'debit',
        category: 'Housing',
        date: new Date(currentDate.setHours(0, 0)).toISOString(),
        status: 'completed',
        merchant: 'Property Management',
        recurring: true,
        tags: ['rent', 'recurring', 'housing'],
      });
      _runningBalance -= 1500;
    }

    if (day === 5) {
      // Utilities
      const utilityAmount = 80 + Math.random() * 40;
      transactions.push({
        id: `trans-${transactions.length + 1}`,
        description: 'Electric Bill',
        amount: utilityAmount,
        type: 'debit',
        category: 'Utilities',
        date: new Date(currentDate.setHours(0, 0)).toISOString(),
        status: 'completed',
        merchant: MERCHANT_POOLS.utility[0],
        recurring: true,
        tags: ['utilities', 'recurring'],
      });
      _runningBalance -= utilityAmount;
    }

    // Add pending transaction occasionally
    if (Math.random() > 0.9 && day < 3) {
      const pendingAmount = 20 + Math.random() * 50;
      transactions.push({
        id: `trans-${transactions.length + 1}`,
        description: 'Online Purchase',
        amount: pendingAmount,
        type: 'debit',
        category: 'Shopping',
        date: currentDate.toISOString(),
        status: 'pending',
        merchant: 'Amazon',
        tags: ['online', 'pending'],
      });
    }
  }

  return transactions.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

// Generate demo notifications
export function generateDemoNotifications(): DemoNotification[] {
  const notifications: DemoNotification[] = [
    {
      id: 'notif-1',
      type: 'success',
      title: 'Payment Received',
      message: 'You received $150 from John Smith',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
      read: false,
      actionUrl: '/transactions',
      actionLabel: 'View Transaction',
    },
    {
      id: 'notif-2',
      type: 'warning',
      title: 'Low Balance Alert',
      message: 'Your Checking account balance is below $500',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
      read: false,
      actionUrl: '/accounts',
      actionLabel: 'View Account',
    },
    {
      id: 'notif-3',
      type: 'info',
      title: 'New Feature Available',
      message: 'Virtual cards are now available for online shopping',
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
      read: true,
      actionUrl: '/cards',
      actionLabel: 'Learn More',
    },
    {
      id: 'notif-4',
      type: 'alert',
      title: 'Unusual Activity',
      message: 'Large purchase detected at Electronics Store for $899',
      timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
      read: false,
      actionUrl: '/security',
      actionLabel: 'Review Activity',
    },
    {
      id: 'notif-5',
      type: 'success',
      title: 'Goal Milestone Reached',
      message: 'You\'ve saved 50% of your Vacation Fund goal!',
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000), // 5 hours ago
      read: true,
      actionUrl: '/goals',
      actionLabel: 'View Progress',
    },
  ];

  return notifications;
}

// Generate demo goals with various progress states
export function generateDemoGoals(): DemoGoal[] {
  return [
    {
      id: 'goal-1',
      name: 'Emergency Fund',
      targetAmount: 10000,
      currentAmount: 7500,
      deadline: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString(), // 6 months
      category: 'emergency',
      color: 'var(--primary-emerald)',
      milestones: [
        { percentage: 25, reached: true, reachedDate: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString() },
        { percentage: 50, reached: true, reachedDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString() },
        { percentage: 75, reached: true, reachedDate: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() },
        { percentage: 100, reached: false },
      ],
    },
    {
      id: 'goal-2',
      name: 'Summer Vacation',
      targetAmount: 3000,
      currentAmount: 1200,
      deadline: new Date(Date.now() + 120 * 24 * 60 * 60 * 1000).toISOString(), // 4 months
      category: 'vacation',
      color: 'var(--primary-blue)',
      milestones: [
        { percentage: 25, reached: true, reachedDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString() },
        { percentage: 50, reached: false },
        { percentage: 75, reached: false },
        { percentage: 100, reached: false },
      ],
    },
    {
      id: 'goal-3',
      name: 'New Laptop',
      targetAmount: 1500,
      currentAmount: 1500,
      deadline: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(), // Completed
      category: 'purchase',
      color: 'var(--primary-indigo)',
      milestones: [
        { percentage: 25, reached: true, reachedDate: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString() },
        { percentage: 50, reached: true, reachedDate: new Date(Date.now() - 40 * 24 * 60 * 60 * 1000).toISOString() },
        { percentage: 75, reached: true, reachedDate: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString() },
        { percentage: 100, reached: true, reachedDate: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString() },
      ],
    },
    {
      id: 'goal-4',
      name: 'Investment Portfolio',
      targetAmount: 25000,
      currentAmount: 5000,
      deadline: new Date(Date.now() + 730 * 24 * 60 * 60 * 1000).toISOString(), // 2 years
      category: 'investment',
      color: 'var(--primary-teal)',
      milestones: [
        { percentage: 25, reached: false },
        { percentage: 50, reached: false },
        { percentage: 75, reached: false },
        { percentage: 100, reached: false },
      ],
    },
  ];
}

// Generate account states for demo
export function generateDemoAccountStates() {
  return {
    lowBalance: {
      checking: {
        balance: 234.56,
        alert: 'Balance below $500',
        alertType: 'warning',
      },
    },
    highCreditUtilization: {
      credit: {
        balance: 4500,
        limit: 5000,
        utilization: 90,
        alert: 'High credit utilization',
        alertType: 'danger',
      },
    },
    healthyAccounts: {
      checking: {
        balance: 3456.78,
        trend: '+12.4%',
      },
      savings: {
        balance: 15234.56,
        trend: '+5.2%',
        interestRate: '4.5% APY',
      },
    },
  };
}