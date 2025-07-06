'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { InsuranceClaim } from '@/types';
import { Card } from '@/components/ui/Card';
import { formatCurrency } from '@/lib/utils';

interface ClaimsListProps {
  claims: InsuranceClaim[];
  onClaimClick?: (claim: InsuranceClaim) => void;
  className?: string;
}

export const ClaimsList: React.FC<ClaimsListProps> = ({ 
  claims, 
  onClaimClick,
  className = '' 
}) => {
  const handleClaimClick = (claim: InsuranceClaim) => {
    onClaimClick?.(claim);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'var(--text-2)';
      case 'submitted':
        return 'var(--primary-blue)';
      case 'under_review':
        return 'var(--primary-yellow)';
      case 'approved':
        return 'var(--primary-emerald)';
      case 'denied':
        return 'var(--primary-red)';
      case 'paid':
        return 'var(--primary-emerald)';
      case 'closed':
        return 'var(--text-3)';
      default:
        return 'var(--text-2)';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft':
        return '📝';
      case 'submitted':
        return '📤';
      case 'under_review':
        return '🔍';
      case 'approved':
        return '✅';
      case 'denied':
        return '❌';
      case 'paid':
        return '💰';
      case 'closed':
        return '📁';
      default:
        return '📄';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const calculateDaysInStatus = (claim: InsuranceClaim) => {
    const lastUpdate = claim.timeline[claim.timeline.length - 1]?.date || claim.filedDate;
    const lastUpdateDate = new Date(lastUpdate);
    const today = new Date();
    const diffTime = today.getTime() - lastUpdateDate.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {claims.map((claim, index) => (
        <motion.div
          key={claim.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          whileHover={{ scale: 1.01 }}
          onClick={() => handleClaimClick(claim)}
          className="cursor-pointer"
        >
          <Card className="p-6 hover:shadow-lg transition-all duration-200">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-3">
                <div className="text-2xl mt-1">{getStatusIcon(claim.status)}</div>
                <div>
                  <h4 className="text-lg font-semibold text-[var(--text-1)]">
                    Claim #{claim.claimNumber}
                  </h4>
                  <p className="text-sm text-[var(--text-2)] capitalize">
                    {claim.claimType.replace(/_/g, ' ')}
                  </p>
                </div>
              </div>
              
              <div 
                className="px-3 py-1 rounded-full text-xs font-medium capitalize"
                style={{ 
                  backgroundColor: `${getStatusColor(claim.status)}20`,
                  color: getStatusColor(claim.status)
                }}
              >
                {claim.status.replace(/_/g, ' ')}
              </div>
            </div>

            <p className="text-sm text-[var(--text-2)] mb-4 line-clamp-2">
              {claim.description}
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-xs text-[var(--text-3)]">Claim Amount</p>
                <p className="text-base font-semibold text-[var(--text-1)]">
                  {formatCurrency(claim.claimAmount)}
                </p>
              </div>
              
              {claim.approvedAmount !== undefined && (
                <div>
                  <p className="text-xs text-[var(--text-3)]">Approved</p>
                  <p className="text-base font-semibold text-[var(--primary-emerald)]">
                    {formatCurrency(claim.approvedAmount)}
                  </p>
                </div>
              )}
              
              {claim.paidAmount !== undefined && (
                <div>
                  <p className="text-xs text-[var(--text-3)]">Paid</p>
                  <p className="text-base font-semibold text-[var(--primary-emerald)]">
                    {formatCurrency(claim.paidAmount)}
                  </p>
                </div>
              )}
              
              <div>
                <p className="text-xs text-[var(--text-3)]">Incident Date</p>
                <p className="text-base font-medium text-[var(--text-1)]">
                  {formatDate(claim.dateOfIncident)}
                </p>
              </div>
            </div>

            {claim.adjuster && (
              <div className="p-3 bg-[rgba(var(--glass-rgb),0.2)] rounded-lg mb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[var(--text-3)]">Adjuster</p>
                    <p className="text-sm font-medium text-[var(--text-1)]">
                      {claim.adjuster.name}
                    </p>
                  </div>
                  <p className="text-sm text-[var(--text-2)]">
                    {claim.adjuster.contact}
                  </p>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-4">
                <span className="text-[var(--text-3)]">
                  Filed: {formatDate(claim.filedDate)}
                </span>
                {claim.documents.length > 0 && (
                  <span className="flex items-center gap-1 text-[var(--text-2)]">
                    📎 {claim.documents.length} document{claim.documents.length > 1 ? 's' : ''}
                  </span>
                )}
              </div>
              
              {claim.status === 'under_review' && (
                <span className="text-xs text-[var(--primary-yellow)]">
                  {calculateDaysInStatus(claim)} days in review
                </span>
              )}
            </div>

            {claim.paymentInfo && (
              <div className="mt-3 p-2 bg-[var(--primary-emerald)]10 rounded border border-[var(--primary-emerald)]30">
                <p className="text-xs text-[var(--primary-emerald)] text-center">
                  💳 Paid on {formatDate(claim.paymentInfo.date)} via {claim.paymentInfo.method}
                </p>
              </div>
            )}
          </Card>
        </motion.div>
      ))}
    </div>
  );
};
