import React from 'react';
import { motion } from 'framer-motion';
import { 
  ShoppingBag, 
  Coffee, 
  Car, 
  Home,
  Zap,
  Music,
  DollarSign,
  ArrowUpRight,
  Clock
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { useRouter } from 'next/navigation';

interface Transaction {
  id: string;
  description: string;
  amount: number;
  type: 'credit' | 'debit';
  category: string;
  date: string;
  status: 'completed' | 'pending';
}

interface RecentTransactionsProps {
  transactions: Transaction[];
  analyticsId?: string;
  analyticsLabel?: string;
}

export const RecentTransactions: React.FC<RecentTransactionsProps> = ({ 
  transactions,
  analyticsId = 'recent-transactions',
  analyticsLabel = 'Recent Transactions',
}) => {
  const router = useRouter();
  const getCategoryIcon = (category: string) => {
    const iconMap: { [key: string]: React.ReactNode } = {
      'Shopping': <ShoppingBag className="w-4 h-4" />,
      'Food & Dining': <Coffee className="w-4 h-4" />,
      'Transportation': <Car className="w-4 h-4" />,
      'Housing': <Home className="w-4 h-4" />,
      'Utilities': <Zap className="w-4 h-4" />,
      'Entertainment': <Music className="w-4 h-4" />,
      'Income': <DollarSign className="w-4 h-4" />,
      'Transfer': <ArrowUpRight className="w-4 h-4" />,
    };
    return iconMap[category] || <DollarSign className="w-4 h-4" />;
  };

  const getCategoryColor = (category: string) => {
    const colorMap: { [key: string]: string } = {
      'Shopping': 'bg-[var(--cat-indigo)]',
      'Food & Dining': 'bg-[var(--cat-amber)]',
      'Transportation': 'bg-[var(--cat-blue)]',
      'Housing': 'bg-[var(--cat-emerald)]',
      'Utilities': 'bg-[var(--cat-teal)]',
      'Entertainment': 'bg-[var(--cat-pink)]',
      'Income': 'bg-[var(--cat-emerald)]',
      'Transfer': 'bg-[var(--cat-blue)]',
    };
    return colorMap[category] || 'bg-[rgba(var(--glass-rgb),0.3)]';
  };

  const formatAmount = (amount: number, type: 'credit' | 'debit') => {
    const sign = type === 'credit' ? '+' : '';
    return `${sign}$${Math.abs(amount).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  return (
    <Card variant="default" className="h-full">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-[var(--text-1)]">
            Recent Transactions
          </h3>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => {
              router.push('/transactions');
            }}
            analyticsId={`${analyticsId}-view-all`}
            analyticsLabel={`${analyticsLabel} View All`}
          >
            View All
          </Button>
        </div>

        <div className="space-y-3">
          {transactions.map((transaction, index) => (
            <motion.div
              key={transaction.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-[rgba(var(--glass-rgb),0.1)] transition-colors cursor-pointer"
              onClick={() => {
                router.push('/transactions');
              }}
            >
              <div className={`
                p-2.5 rounded-lg ${getCategoryColor(transaction.category)}
                flex items-center justify-center
              `}>
                {getCategoryIcon(transaction.category)}
              </div>

              <div className="flex-1 min-w-0">
                <p className="font-medium text-[var(--text-1)] truncate">
                  {transaction.description}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-xs text-[var(--text-2)]">
                    {transaction.category}
                  </p>
                  {transaction.status === 'pending' && (
                    <>
                      <span className="text-[var(--text-2)]">•</span>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-[var(--primary-amber)]" />
                        <span className="text-xs text-[var(--primary-amber)]">
                          Pending
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              <div className="text-right">
                <p className={`font-semibold ${
                  transaction.type === 'credit'
                    ? 'text-[var(--primary-emerald)]'
                    : 'text-[var(--text-1)]'
                }`}>
                  {formatAmount(transaction.amount, transaction.type)}
                </p>
                <p className="text-xs text-[var(--text-2)] mt-1">
                  {formatDate(transaction.date)}
                </p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Load More */}
        <div className="mt-4 pt-4 border-t border-[var(--border-1)]">
          <Button 
            variant="secondary" 
            size="sm" 
            fullWidth
            onClick={() => {
              
            }}
            analyticsId={`${analyticsId}-load-more`}
            analyticsLabel={`${analyticsLabel} Load More`}
          >
            Load More Transactions
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default RecentTransactions;
