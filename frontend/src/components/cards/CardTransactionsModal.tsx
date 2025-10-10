import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  
  Download,
  CreditCard,
  ShoppingBag,
  Coffee,
  Car,
  Home,
  Heart,
  Zap,
  DollarSign
} from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import { cardsApi } from '@/lib/api';

interface Transaction {
  id: number;
  amount: number;
  description: string;
  transaction_date: string;
  merchant: string;
  category: string;
  status: string;
}

interface CardTransactionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  cardId: string;
  cardName: string;
  lastFour: string;
}

export const CardTransactionsModal: React.FC<CardTransactionsModalProps> = ({
  isOpen,
  onClose,
  cardId,
  cardName,
  lastFour
}) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    if (isOpen) {
      fetchTransactions();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, cardId]);

  const fetchTransactions = async () => {
    try {
      setIsLoading(true);
      const data = await cardsApi.getCardTransactions(parseInt(cardId));
      setTransactions(data);
    } catch {
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: React.ReactNode } = {
      'Shopping': <ShoppingBag className="w-4 h-4" />,
      'Food & Dining': <Coffee className="w-4 h-4" />,
      'Transportation': <Car className="w-4 h-4" />,
      'Utilities': <Home className="w-4 h-4" />,
      'Healthcare': <Heart className="w-4 h-4" />,
      'Entertainment': <Zap className="w-4 h-4" />,
      'Other': <DollarSign className="w-4 h-4" />
    };
    return icons[category] || <DollarSign className="w-4 h-4" />;
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Shopping': 'text-[var(--primary-indigo)] bg-[rgba(var(--primary-indigo-rgb),0.1)]',
      'Food & Dining': 'text-[var(--primary-amber)] bg-[rgba(var(--primary-amber-rgb),0.1)]',
      'Transportation': 'text-[var(--primary-blue)] bg-[rgba(var(--primary-blue-rgb),0.1)]',
      'Utilities': 'text-[var(--primary-emerald)] bg-[rgba(var(--primary-emerald-rgb),0.1)]',
      'Healthcare': 'text-[var(--primary-pink)] bg-[rgba(var(--primary-pink-rgb),0.1)]',
      'Entertainment': 'text-[var(--primary-violet)] bg-[rgba(var(--primary-violet-rgb),0.1)]',
      'Other': 'text-[var(--text-2)] bg-[rgba(var(--glass-rgb),0.1)]'
    };
    return colors[category] || 'text-[var(--text-2)] bg-[rgba(var(--glass-rgb),0.1)]';
  };

  const filteredTransactions = transactions.filter(transaction => {
    const matchesSearch = transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transaction.merchant.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || transaction.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = ['all', ...Array.from(new Set(transactions.map(t => t.category)))];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Transactions - ${cardName}`}
      size="lg"
    >
      <div className="space-y-4">
        {/* Header Info */}
        <div className="flex items-center gap-3 p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)]">
          <div className="p-2 rounded-lg bg-[rgba(var(--primary-blue-rgb),0.1)]">
            <CreditCard className="w-5 h-5 text-[var(--primary-blue)]" />
          </div>
          <div>
            <p className="font-medium text-[var(--text-1)]">{cardName}</p>
            <p className="text-sm text-[var(--text-2)]">•••• {lastFour}</p>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-2)]" />
            <input
              type="text"
              placeholder="Search transactions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)] rounded-lg text-[var(--text-1)] placeholder-[var(--text-2)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)] focus:border-transparent"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)] rounded-lg text-[var(--text-1)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)] focus:border-transparent"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat}
              </option>
            ))}
          </select>
        </div>

        {/* Transactions List */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-blue)] mx-auto"></div>
              <p className="mt-2 text-[var(--text-2)]">Loading transactions...</p>
            </div>
          ) : filteredTransactions.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-[var(--text-2)]">No transactions found</p>
            </div>
          ) : (
            <AnimatePresence>
              {filteredTransactions.map((transaction, index) => (
                <motion.div
                  key={transaction.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: index * 0.02 }}
                  className="flex items-center justify-between p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] hover:bg-[rgba(var(--glass-rgb),0.1)] transition-colors cursor-pointer"
                  onClick={() => {}}>
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${getCategoryColor(transaction.category)}`}>
                      {getCategoryIcon(transaction.category)}
                    </div>
                    <div>
                      <p className="font-medium text-[var(--text-1)]">{transaction.description}</p>
                      <p className="text-sm text-[var(--text-2)]">
                        {transaction.merchant} • {formatDate(transaction.transaction_date)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold ${transaction.amount < 0 ? 'text-[var(--primary-emerald)]' : 'text-[var(--text-1)]'}`}>
                      {transaction.amount < 0 ? '+' : '-'}{formatCurrency(Math.abs(transaction.amount))}
                    </p>
                    <p className="text-xs text-[var(--text-2)] capitalize">{transaction.status}</p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-3 pt-4 border-t border-[var(--border-1)]">
          <div className="text-center">
            <p className="text-sm text-[var(--text-2)]">Total Spent</p>
            <p className="text-lg font-semibold text-[var(--text-1)]">
              {formatCurrency(transactions.filter(t => t.amount > 0).reduce((sum, t) => sum + t.amount, 0))}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-[var(--text-2)]">Transactions</p>
            <p className="text-lg font-semibold text-[var(--text-1)]">
              {transactions.length}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-[var(--text-2)]">Avg. Transaction</p>
            <p className="text-lg font-semibold text-[var(--text-1)]">
              {formatCurrency(
                transactions.length > 0 
                  ? transactions.reduce((sum, t) => sum + Math.abs(t.amount), 0) / transactions.length
                  : 0
              )}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Button
            variant="secondary"
            size="sm"
            icon={<Download size={16} />}
            onClick={() => {
              // Implement download functionality
            }}
          >
            Export
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={onClose}
          >
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default CardTransactionsModal;
