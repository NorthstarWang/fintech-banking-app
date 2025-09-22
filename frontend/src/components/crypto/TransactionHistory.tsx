'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CryptoTransaction } from '@/types';
import { formatCurrency } from '@/lib/utils';

interface TransactionHistoryProps {
  transactions: CryptoTransaction[];
  onTransactionClick?: (transaction: CryptoTransaction) => void;
  className?: string;
}

export const TransactionHistory: React.FC<TransactionHistoryProps> = ({ 
  transactions, 
  onTransactionClick,
  className = '' 
}) => {
  const handleTransactionClick = (transaction: CryptoTransaction) => {
    onTransactionClick?.(transaction);
  };

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'send':
        return '↗️';
      case 'receive':
        return '↙️';
      case 'swap':
        return '🔄';
      case 'stake':
        return '🔒';
      case 'unstake':
        return '🔓';
      case 'mint':
        return '✨';
      case 'burn':
        return '🔥';
      default:
        return '📝';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'var(--primary-emerald)';
      case 'pending':
        return 'var(--primary-yellow)';
      case 'failed':
        return 'var(--primary-red)';
      default:
        return 'var(--text-2)';
    }
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffMins < 1440) {
      return `${Math.floor(diffMins / 60)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className={`space-y-3 ${className}`}>
      {transactions.map((tx, index) => (
        <motion.div
          key={tx.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
          whileHover={{ scale: 1.01 }}
          onClick={() => handleTransactionClick(tx)}
          className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.3)] backdrop-blur-sm border border-[var(--glass-border)] cursor-pointer hover:bg-[rgba(var(--glass-rgb),0.5)] transition-all duration-200"
        >
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="text-2xl">{getTransactionIcon(tx.type)}</div>
              <div>
                <h4 className="font-semibold text-[var(--text-1)] capitalize">
                  {tx.type}
                </h4>
                <p className="text-sm text-[var(--text-2)]">
                  {tx.type === 'send' ? `To ${formatAddress(tx.toAddress)}` : 
                   tx.type === 'receive' ? `From ${formatAddress(tx.fromAddress)}` :
                   tx.type === 'swap' ? 'Token Swap' : 
                   tx.network}
                </p>
              </div>
            </div>

            <div className="text-right">
              <p className="font-semibold text-[var(--text-1)]">
                {tx.type === 'send' ? '-' : '+'}{formatCurrency(tx.amountUSD)}
              </p>
              <p className="text-sm text-[var(--text-3)]">
                {tx.amount.toFixed(6)}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-3">
              <span 
                className="px-2 py-1 rounded-full text-xs font-medium"
                style={{
                  backgroundColor: `${getStatusColor(tx.status)}20`,
                  color: getStatusColor(tx.status)
                }}
              >
                {tx.status}
              </span>
              <span className="text-[var(--text-3)]">
                {formatDate(tx.timestamp)}
              </span>
            </div>

            <div className="flex items-center gap-2 text-[var(--text-3)]">
              <span>Gas: {formatCurrency(tx.gasFeeUSD)}</span>
              {tx.confirmations !== undefined && (
                <span className="text-xs">
                  {tx.confirmations} confirmations
                </span>
              )}
            </div>
          </div>

          {tx.txHash && (
            <div className="mt-2 pt-2 border-t border-[var(--glass-border)]">
              <p className="text-xs text-[var(--text-3)] font-mono truncate">
                {tx.txHash}
              </p>
            </div>
          )}
        </motion.div>
      ))}
    </div>
  );
};
