'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Loan } from '@/types';
import { Card } from '@/components/ui/Card';
import { formatCurrency } from '@/lib/utils';

interface LoanCardProps {
  loan: Loan;
  onClick?: () => void;
  showDetails?: boolean;
  className?: string;
}

export const LoanCard: React.FC<LoanCardProps> = ({ 
  loan, 
  onClick, 
  showDetails = true,
  className = '' 
}) => {
  const handleClick = () => {
    onClick?.();
  };

  const getLoanIcon = () => {
    switch (loan.loanType) {
      case 'mortgage':
        return '🏠';
      case 'auto':
        return '🚗';
      case 'personal':
        return '💰';
      case 'student':
        return '🎓';
      case 'business':
        return '💼';
      case 'crypto_backed':
        return '🔗';
      default:
        return '📄';
    }
  };

  const getStatusColor = () => {
    switch (loan.status) {
      case 'active':
        return 'var(--primary-blue)';
      case 'paid_off':
        return 'var(--primary-emerald)';
      case 'defaulted':
        return 'var(--primary-red)';
      case 'refinanced':
        return 'var(--primary-purple)';
      default:
        return 'var(--text-2)';
    }
  };

  const calculateProgress = () => {
    const paidAmount = loan.principal - loan.balance;
    return (paidAmount / loan.principal) * 100;
  };

  const daysUntilNextPayment = () => {
    const nextPayment = new Date(loan.nextPaymentDate);
    const today = new Date();
    const diffTime = nextPayment.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={handleClick}
      className={className}
    >
      <Card className="p-6 cursor-pointer hover:shadow-lg transition-all duration-200">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="text-3xl">{getLoanIcon()}</div>
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-1)] capitalize">
                {loan.loanType.replace('_', ' ')} Loan
              </h3>
              <p className="text-sm text-[var(--text-2)]">{loan.lender}</p>
            </div>
          </div>
          <div 
            className="px-3 py-1 rounded-full text-xs font-medium capitalize"
            style={{ 
              backgroundColor: `${getStatusColor()}20`,
              color: getStatusColor()
            }}
          >
            {loan.status.replace('_', ' ')}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-[var(--text-2)]">Current Balance</p>
            <p className="text-xl font-bold text-[var(--text-1)]">
              {formatCurrency(loan.balance)}
            </p>
          </div>
          <div>
            <p className="text-sm text-[var(--text-2)]">Monthly Payment</p>
            <p className="text-xl font-bold text-[var(--text-1)]">
              {formatCurrency(loan.monthlyPayment)}
            </p>
          </div>
        </div>

        {showDetails && (
          <>
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-[var(--text-2)]">Progress</span>
                <span className="text-sm font-medium text-[var(--text-1)]">
                  {calculateProgress().toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-[var(--glass-bg)] rounded-full h-2">
                <motion.div
                  className="h-full rounded-full gradient-primary"
                  initial={{ width: 0 }}
                  animate={{ width: `${calculateProgress()}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-[var(--text-3)]">Interest Rate</p>
                <p className="font-medium text-[var(--text-1)]">{loan.interestRate.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-[var(--text-3)]">Term</p>
                <p className="font-medium text-[var(--text-1)]">{loan.term} months</p>
              </div>
              <div>
                <p className="text-[var(--text-3)]">Original Amount</p>
                <p className="font-medium text-[var(--text-1)]">{formatCurrency(loan.principal)}</p>
              </div>
              <div>
                <p className="text-[var(--text-3)]">Next Payment</p>
                <p className="font-medium text-[var(--text-1)]">
                  {daysUntilNextPayment() > 0 ? `${daysUntilNextPayment()} days` : 'Due today'}
                </p>
              </div>
            </div>

            {loan.refinanceEligible && loan.status === 'active' && (
              <div className="mt-4 p-3 bg-[var(--primary-blue)]10 rounded-lg border border-[var(--primary-blue)]30">
                <p className="text-sm text-[var(--primary-blue)] text-center">
                  ✨ Refinance options available
                </p>
              </div>
            )}

            {loan.collateral && (
              <div className="mt-4 p-3 bg-[rgba(var(--glass-rgb),0.2)] rounded-lg">
                <p className="text-xs text-[var(--text-3)] mb-1">Collateral</p>
                <p className="text-sm text-[var(--text-1)]">
                  {loan.collateral.type}: {formatCurrency(loan.collateral.value)}
                </p>
              </div>
            )}
          </>
        )}
      </Card>
    </motion.div>
  );
};
