'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { LoanPaymentSchedule } from '@/types';
import { Card } from '@/components/ui/Card';
import { formatCurrency } from '@/lib/utils';

interface PaymentScheduleProps {
  schedule: LoanPaymentSchedule[];
  onPaymentClick?: (payment: LoanPaymentSchedule) => void;
  className?: string;
}

export const PaymentSchedule: React.FC<PaymentScheduleProps> = ({ 
  schedule, 
  onPaymentClick,
  className = '' 
}) => {
  const upcomingPayments = schedule.filter(p => p.status === 'scheduled').slice(0, 6);
  const pastPayments = schedule.filter(p => p.status !== 'scheduled');

  const handlePaymentClick = (payment: LoanPaymentSchedule) => {
    onPaymentClick?.(payment);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'var(--primary-emerald)';
      case 'late':
        return 'var(--primary-yellow)';
      case 'missed':
        return 'var(--primary-red)';
      default:
        return 'var(--text-2)';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const [showAll, setShowAll] = React.useState(false);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Upcoming Payments */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-[var(--text-1)] mb-4">Upcoming Payments</h3>
        
        <div className="space-y-3">
          {upcomingPayments.map((payment, index) => (
            <motion.div
              key={payment.paymentNumber}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => handlePaymentClick(payment)}
              className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.2)] cursor-pointer hover:bg-[rgba(var(--glass-rgb),0.3)] transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-medium text-[var(--text-1)]">
                    Payment #{payment.paymentNumber}
                  </p>
                  <p className="text-sm text-[var(--text-2)]">
                    Due {formatDate(payment.dueDate)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-[var(--text-1)]">
                    {formatCurrency(payment.payment)}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-[var(--text-3)]">Principal</p>
                  <p className="font-medium text-[var(--text-1)]">
                    {formatCurrency(payment.principal)}
                  </p>
                </div>
                <div>
                  <p className="text-[var(--text-3)]">Interest</p>
                  <p className="font-medium text-[var(--text-1)]">
                    {formatCurrency(payment.interest)}
                  </p>
                </div>
                <div>
                  <p className="text-[var(--text-3)]">Balance After</p>
                  <p className="font-medium text-[var(--text-1)]">
                    {formatCurrency(payment.balance)}
                  </p>
                </div>
              </div>

              {index === 0 && (
                <motion.div 
                  className="mt-3 p-2 bg-[var(--primary-blue)]10 rounded border border-[var(--primary-blue)]30"
                  initial={{ scale: 0.9 }}
                  animate={{ scale: 1 }}
                  transition={{ repeat: Infinity, duration: 2, repeatType: "reverse" }}
                >
                  <p className="text-xs text-[var(--primary-blue)] text-center">Next Payment Due</p>
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </Card>

      {/* Payment History */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-[var(--text-1)]">Payment History</h3>
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-sm text-[var(--primary-blue)] hover:text-[var(--primary-blue-hover)] transition-colors"
            data-testid="toggle-payment-history"
          >
            {showAll ? 'Show Less' : 'Show All'}
          </button>
        </div>
        
        <div className="space-y-2">
          {(showAll ? pastPayments : pastPayments.slice(0, 5)).map((payment, index) => (
            <motion.div
              key={payment.paymentNumber}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.03 }}
              onClick={() => handlePaymentClick(payment)}
              className="p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] cursor-pointer hover:bg-[rgba(var(--glass-rgb),0.2)] transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div 
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: getStatusColor(payment.status) }}
                  />
                  <div>
                    <p className="text-sm font-medium text-[var(--text-1)]">
                      Payment #{payment.paymentNumber}
                    </p>
                    <p className="text-xs text-[var(--text-3)]">
                      {payment.paidDate ? formatDate(payment.paidDate) : formatDate(payment.dueDate)}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className="text-sm font-medium text-[var(--text-1)]">
                    {formatCurrency(payment.paidAmount || payment.payment)}
                  </p>
                  <p 
                    className="text-xs capitalize"
                    style={{ color: getStatusColor(payment.status) }}
                  >
                    {payment.status}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </Card>

      {/* Payment Summary */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-[var(--text-1)] mb-4">Payment Summary</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-[rgba(var(--glass-rgb),0.2)] rounded-lg">
            <p className="text-sm text-[var(--text-2)] mb-1">Total Paid</p>
            <p className="text-xl font-bold text-[var(--primary-emerald)]">
              {formatCurrency(
                pastPayments
                  .filter(p => p.status === 'paid')
                  .reduce((sum, p) => sum + (p.paidAmount || p.payment), 0)
              )}
            </p>
          </div>
          
          <div className="p-3 bg-[rgba(var(--glass-rgb),0.2)] rounded-lg">
            <p className="text-sm text-[var(--text-2)] mb-1">On-Time Payments</p>
            <p className="text-xl font-bold text-[var(--text-1)]">
              {pastPayments.filter(p => p.status === 'paid').length} / {pastPayments.length}
            </p>
          </div>
          
          <div className="p-3 bg-[rgba(var(--glass-rgb),0.2)] rounded-lg">
            <p className="text-sm text-[var(--text-2)] mb-1">Interest Paid</p>
            <p className="text-xl font-bold text-[var(--text-1)]">
              {formatCurrency(
                pastPayments
                  .filter(p => p.status === 'paid')
                  .reduce((sum, p) => sum + p.interest, 0)
              )}
            </p>
          </div>
          
          <div className="p-3 bg-[rgba(var(--glass-rgb),0.2)] rounded-lg">
            <p className="text-sm text-[var(--text-2)] mb-1">Principal Paid</p>
            <p className="text-xl font-bold text-[var(--text-1)]">
              {formatCurrency(
                pastPayments
                  .filter(p => p.status === 'paid')
                  .reduce((sum, p) => sum + p.principal, 0)
              )}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
