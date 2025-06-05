'use client';

import { useState, useCallback, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import OptimizedTransactionList from '@/components/transactions/OptimizedTransactionList';
import TransactionDetail from '@/components/transactions/TransactionDetail';
import TransactionFilters from '@/components/transactions/TransactionFilters';
import { DebouncedInput } from '@/components/performance/OptimizedComponents';
import LoadingSkeleton from '@/components/performance/LoadingSkeleton';
import { useOptimizedQuery } from '@/hooks/useOptimizedQuery';
import { performanceMonitor } from '@/utils/PerformanceMonitor';
import { api } from '@/lib/api';
import { Search } from 'lucide-react';

// Types remain the same...
export interface UITransaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  type: 'credit' | 'debit';
  category: string;
  subcategory?: string;
  merchant: string;
  location?: string;
  accountId: string;
  accountName: string;
  accountType: string;
  balance?: number;
  status: 'completed' | 'pending' | 'failed';
  attachments?: number;
  tags?: string[];
  notes?: string;
}

export default function OptimizedTransactionsPage() {
  const [selectedTransaction, setSelectedTransaction] = useState<UITransaction | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    dateRange: 'all',
    categories: [] as string[],
    accounts: [] as string[],
    types: [] as string[],
    statuses: [] as string[],
    minAmount: '',
    maxAmount: '',
  });

  // Track page performance
  useEffect(() => {
    performanceMonitor.mark('transactions-page-mount');
    return () => {
      performanceMonitor.measure('transactions-page', 'transactions-page-mount');
    };
  }, []);

  // Use optimized query hook
  const { data: transactions = [], isLoading, error, refetch } = useOptimizedQuery<UITransaction[]>({
    queryKey: ['transactions', filters, searchTerm],
    queryFn: async () => {
      performanceMonitor.mark('fetch-transactions-start');
      
      try {
        const response = await api.transactions.getAll({
          search: searchTerm,
          ...filters
        });
        
        performanceMonitor.measure('fetch-transactions', 'fetch-transactions-start');
        return response.data;
      } catch (error) {
        console.error('Failed to fetch transactions:', error);
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: true,
  });

  // Memoized filtered transactions
  const filteredTransactions = useMemo(() => {
    performanceMonitor.mark('filter-transactions-start');
    
    let filtered = transactions;

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(t => 
        t.description.toLowerCase().includes(searchLower) ||
        t.merchant.toLowerCase().includes(searchLower) ||
        t.category.toLowerCase().includes(searchLower) ||
        t.accountName.toLowerCase().includes(searchLower)
      );
    }

    // Apply other filters...
    if (filters.categories.length > 0) {
      filtered = filtered.filter(t => filters.categories.includes(t.category));
    }

    if (filters.accounts.length > 0) {
      filtered = filtered.filter(t => filters.accounts.includes(t.accountId));
    }

    if (filters.types.length > 0) {
      filtered = filtered.filter(t => filters.types.includes(t.type));
    }

    if (filters.statuses.length > 0) {
      filtered = filtered.filter(t => filters.statuses.includes(t.status));
    }

    if (filters.minAmount) {
      const min = parseFloat(filters.minAmount);
      filtered = filtered.filter(t => t.amount >= min);
    }

    if (filters.maxAmount) {
      const max = parseFloat(filters.maxAmount);
      filtered = filtered.filter(t => t.amount <= max);
    }

    performanceMonitor.measure('filter-transactions', 'filter-transactions-start');
    return filtered;
  }, [transactions, searchTerm, filters]);

  const handleSearchChange = useCallback((value: string) => {
    setSearchTerm(value);
  }, []);

  const handleFilterChange = useCallback((newFilters: typeof filters) => {
    setFilters(newFilters);
  }, []);

  const handleSelectTransaction = useCallback((transaction: UITransaction) => {
    setSelectedTransaction(transaction);
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 100
      }
    }
  };

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <p className="text-red-600">Failed to load transactions</p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text-1)]">Transactions</h1>
        <p className="text-[var(--text-2)] mt-2">
          Track and manage all your financial transactions
        </p>
      </motion.div>

      {/* Search Bar */}
      <motion.div variants={itemVariants} className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--text-2)] w-5 h-5" />
          <DebouncedInput
            type="text"
            placeholder="Search transactions..."
            value={searchTerm}
            onDebouncedChange={handleSearchChange}
            delay={300}
            className="w-full pl-10 pr-4 py-3 rounded-lg bg-[rgba(var(--glass-rgb),0.5)] border border-[rgba(var(--glass-border-rgb),0.3)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)] text-[var(--text-1)]"
          />
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Filters - Left Sidebar */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          {isLoading ? (
            <LoadingSkeleton type="card" height="400px" />
          ) : (
            <TransactionFilters
              filters={filters}
              onFilterChange={handleFilterChange}
              transactions={transactions}
            />
          )}
        </motion.div>

        {/* Transaction List - Center */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          {isLoading ? (
            <LoadingSkeleton type="list" count={5} />
          ) : (
            <OptimizedTransactionList
              transactions={filteredTransactions}
              selectedTransaction={selectedTransaction}
              onSelectTransaction={handleSelectTransaction}
            />
          )}
        </motion.div>

        {/* Transaction Detail - Right Sidebar */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          {isLoading ? (
            <LoadingSkeleton type="card" height="600px" />
          ) : selectedTransaction ? (
            <TransactionDetail
              transaction={selectedTransaction}
              onClose={() => setSelectedTransaction(null)}
            />
          ) : (
            <div className="bg-[rgba(var(--glass-rgb),0.5)] backdrop-blur-lg rounded-xl p-6 text-center">
              <p className="text-[var(--text-2)]">
                Select a transaction to view details
              </p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Summary Stats */}
      {!isLoading && (
        <motion.div 
          variants={itemVariants} 
          className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4"
        >
          <div className="bg-[rgba(var(--glass-rgb),0.5)] backdrop-blur-lg rounded-xl p-4">
            <p className="text-sm text-[var(--text-2)]">Total Transactions</p>
            <p className="text-2xl font-bold text-[var(--text-1)]">
              {filteredTransactions.length}
            </p>
          </div>
          
          <div className="bg-[rgba(var(--glass-rgb),0.5)] backdrop-blur-lg rounded-xl p-4">
            <p className="text-sm text-[var(--text-2)]">Total Income</p>
            <p className="text-2xl font-bold text-[var(--primary-emerald)]">
              ${filteredTransactions
                .filter(t => t.type === 'credit')
                .reduce((sum, t) => sum + t.amount, 0)
                .toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
          
          <div className="bg-[rgba(var(--glass-rgb),0.5)] backdrop-blur-lg rounded-xl p-4">
            <p className="text-sm text-[var(--text-2)]">Total Expenses</p>
            <p className="text-2xl font-bold text-[var(--text-1)]">
              ${filteredTransactions
                .filter(t => t.type === 'debit')
                .reduce((sum, t) => sum + t.amount, 0)
                .toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
          
          <div className="bg-[rgba(var(--glass-rgb),0.5)] backdrop-blur-lg rounded-xl p-4">
            <p className="text-sm text-[var(--text-2)]">Net Flow</p>
            <p className="text-2xl font-bold">
              ${(
                filteredTransactions.filter(t => t.type === 'credit').reduce((sum, t) => sum + t.amount, 0) -
                filteredTransactions.filter(t => t.type === 'debit').reduce((sum, t) => sum + t.amount, 0)
              ).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}