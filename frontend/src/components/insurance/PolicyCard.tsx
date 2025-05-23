'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { InsurancePolicy } from '@/types';
import { Card } from '@/components/ui/Card';
import { formatCurrency } from '@/lib/utils';

interface PolicyCardProps {
  policy: InsurancePolicy;
  onClick?: () => void;
  showDetails?: boolean;
  className?: string;
}

export const PolicyCard: React.FC<PolicyCardProps> = ({ 
  policy, 
  onClick, 
  showDetails = true,
  className = '' 
}) => {
  const handleClick = () => {
    onClick?.();
  };

  const getPolicyIcon = () => {
    switch (policy.policyType) {
      case 'health':
        return '🏥';
      case 'auto':
        return '🚗';
      case 'home':
        return '🏠';
      case 'life':
        return '💗';
      case 'disability':
        return '🦽';
      case 'travel':
        return '✈️';
      case 'pet':
        return '🐾';
      case 'dental':
        return '🦷';
      case 'vision':
        return '👁️';
      default:
        return '📋';
    }
  };

  const getStatusColor = () => {
    switch (policy.status) {
      case 'active':
        return 'var(--primary-emerald)';
      case 'lapsed':
        return 'var(--primary-yellow)';
      case 'cancelled':
        return 'var(--primary-red)';
      case 'expired':
        return 'var(--primary-orange)';
      default:
        return 'var(--text-2)';
    }
  };

  const getPremiumFrequencyText = () => {
    switch (policy.premiumFrequency) {
      case 'monthly':
        return '/month';
      case 'quarterly':
        return '/quarter';
      case 'semi-annual':
        return '/6 months';
      case 'annual':
        return '/year';
      default:
        return '';
    }
  };

  const daysUntilRenewal = () => {
    const renewal = new Date(policy.renewalDate);
    const today = new Date();
    const diffTime = renewal.getTime() - today.getTime();
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
            <div className="text-3xl">{getPolicyIcon()}</div>
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-1)] capitalize">
                {policy.policyType} Insurance
              </h3>
              <p className="text-sm text-[var(--text-2)]">{policy.provider}</p>
            </div>
          </div>
          <div 
            className="px-3 py-1 rounded-full text-xs font-medium capitalize"
            style={{ 
              backgroundColor: `${getStatusColor()}20`,
              color: getStatusColor()
            }}
          >
            {policy.status}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-[var(--text-2)]">Premium</p>
            <p className="text-xl font-bold text-[var(--text-1)]">
              {formatCurrency(policy.premium)}
              <span className="text-sm font-normal text-[var(--text-2)]">
                {getPremiumFrequencyText()}
              </span>
            </p>
          </div>
          <div>
            <p className="text-sm text-[var(--text-2)]">Coverage</p>
            <p className="text-xl font-bold text-[var(--text-1)]">
              {formatCurrency(policy.coverageAmount)}
            </p>
          </div>
        </div>

        {showDetails && (
          <>
            <div className="grid grid-cols-2 gap-4 text-sm mb-4">
              <div>
                <p className="text-[var(--text-3)]">Policy Number</p>
                <p className="font-medium text-[var(--text-1)] font-mono text-xs">
                  {policy.policyNumber}
                </p>
              </div>
              <div>
                <p className="text-[var(--text-3)]">Deductible</p>
                <p className="font-medium text-[var(--text-1)]">
                  {formatCurrency(policy.deductible)}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-[rgba(var(--glass-rgb),0.2)] rounded-lg">
                <span className="text-sm text-[var(--text-2)]">Policy Period</span>
                <span className="text-sm font-medium text-[var(--text-1)]">
                  {new Date(policy.startDate).toLocaleDateString()} - {new Date(policy.endDate).toLocaleDateString()}
                </span>
              </div>

              {policy.status === 'active' && (
                <div className="flex items-center justify-between p-3 bg-[rgba(var(--glass-rgb),0.2)] rounded-lg">
                  <span className="text-sm text-[var(--text-2)]">Renewal</span>
                  <span className="text-sm font-medium text-[var(--text-1)]">
                    {daysUntilRenewal() > 0 ? `${daysUntilRenewal()} days` : 'Due for renewal'}
                  </span>
                </div>
              )}
            </div>

            {policy.beneficiaries && policy.beneficiaries.length > 0 && (
              <div className="mt-4 p-3 bg-[rgba(var(--glass-rgb),0.2)] rounded-lg">
                <p className="text-xs text-[var(--text-3)] mb-2">Beneficiaries</p>
                <div className="space-y-1">
                  {policy.beneficiaries.map((beneficiary, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-[var(--text-2)]">
                        {beneficiary.name} ({beneficiary.relationship})
                      </span>
                      <span className="text-[var(--text-1)] font-medium">
                        {beneficiary.percentage}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {policy.autoRenew && policy.status === 'active' && (
              <div className="mt-3 flex items-center gap-2 text-xs text-[var(--primary-blue)]">
                <span>🔄</span>
                <span>Auto-renewal enabled</span>
              </div>
            )}
          </>
        )}
      </Card>
    </motion.div>
  );
};
