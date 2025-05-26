'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  DollarSign,
  Calendar,
  ShoppingBag,
  AlertCircle,
  Check,
  X,
  TrendingUp,
  Edit2
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { cardsApi } from '@/lib/api';
import type { SpendingLimitResponse, SpendingLimitRequest } from '@/lib/api';

interface SpendingLimitsProps {
  cardId: number;
}

interface CategoryLimit {
  name: string;
  limit: number;
  usage: number;
  icon: React.ReactNode;
  color: string;
}

const SPENDING_CATEGORIES = [
  { value: 'dining', label: 'Dining', icon: '🍽️', color: 'var(--primary-orange)' },
  { value: 'shopping', label: 'Shopping', icon: '🛍️', color: 'var(--primary-pink)' },
  { value: 'travel', label: 'Travel', icon: '✈️', color: 'var(--primary-blue)' },
  { value: 'entertainment', label: 'Entertainment', icon: '🎭', color: 'var(--primary-violet)' },
  { value: 'groceries', label: 'Groceries', icon: '🛒', color: 'var(--primary-emerald)' },
  { value: 'gas', label: 'Gas', icon: '⛽', color: 'var(--primary-yellow)' },
];

export default function SpendingLimits({ cardId }: SpendingLimitsProps) {
  const [limits, setLimits] = useState<SpendingLimitResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [dailyLimit, setDailyLimit] = useState<string>('');
  const [monthlyLimit, setMonthlyLimit] = useState<string>('');
  const [categoryLimits, setCategoryLimits] = useState<Record<string, string>>({});

  useEffect(() => {
    if (cardId && !isNaN(cardId)) {
      fetchLimits();
    }
  }, [cardId]);

  const fetchLimits = async () => {
    if (!cardId || isNaN(cardId)) {
      return;
    }
    
    try {
      setIsLoading(true);
      const data = await cardsApi.getSpendingLimits(cardId);
      setLimits(data);
      
      // Initialize form with current values
      setDailyLimit(data.daily_limit?.toString() || '');
      setMonthlyLimit(data.monthly_limit?.toString() || '');
      
      const catLimits: Record<string, string> = {};
      if (data.category_limits) {
        Object.entries(data.category_limits).forEach(([cat, info]) => {
          catLimits[cat] = info.limit.toString();
        });
      }
      setCategoryLimits(catLimits);
    } catch (err) {
      setError('Failed to load spending limits');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError(null);

      const request: SpendingLimitRequest = {};
      
      if (dailyLimit) {
        request.daily_limit = parseFloat(dailyLimit);
      }
      
      if (monthlyLimit) {
        request.monthly_limit = parseFloat(monthlyLimit);
      }
      
      const catLimits: Record<string, number> = {};
      Object.entries(categoryLimits).forEach(([cat, limit]) => {
        if (limit) {
          catLimits[cat] = parseFloat(limit);
        }
      });
      
      if (Object.keys(catLimits).length > 0) {
        request.category_limits = catLimits;
      }

      await cardsApi.setSpendingLimits(cardId, request);
      await fetchLimits();
      setIsEditing(false);
    } catch (err) {
      setError('Failed to update spending limits');
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const getUsagePercentage = (usage: number, limit: number) => {
    return Math.min((usage / limit) * 100, 100);
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'var(--primary-red)';
    if (percentage >= 75) return 'var(--primary-yellow)';
    return 'var(--primary-emerald)';
  };

  if (isLoading) {
    return (
      <Card variant="default" className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-[rgba(var(--glass-rgb),0.1)] rounded w-1/3"></div>
          <div className="space-y-3">
            <div className="h-12 bg-[rgba(var(--glass-rgb),0.1)] rounded"></div>
            <div className="h-12 bg-[rgba(var(--glass-rgb),0.1)] rounded"></div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card variant="default" className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-[var(--text-1)]">
            Spending Limits
          </h3>
          <Button
            variant="secondary"
            size="sm"
            icon={<Edit2 size={16} />}
            onClick={() => setIsEditing(true)}
          >
            Edit Limits
          </Button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-[var(--error-bg)] border border-[var(--error-border)] rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-[var(--error-text)]" />
            <p className="text-sm text-[var(--error-text)]">{error}</p>
          </div>
        )}

        <div className="space-y-6">
          {/* Daily Limit */}
          {limits?.daily_limit && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-[var(--text-2)]" />
                  <span className="text-sm text-[var(--text-2)]">Daily Limit</span>
                </div>
                <span className="text-sm font-medium text-[var(--text-1)]">
                  ${limits.daily_usage.toFixed(2)} / ${limits.daily_limit.toFixed(2)}
                </span>
              </div>
              <div className="relative h-2 bg-[rgba(var(--glass-rgb),0.1)] rounded-full overflow-hidden">
                <motion.div
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{ 
                    backgroundColor: getUsageColor(getUsagePercentage(limits.daily_usage, limits.daily_limit))
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${getUsagePercentage(limits.daily_usage, limits.daily_limit)}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
              </div>
            </div>
          )}

          {/* Monthly Limit */}
          {limits?.monthly_limit && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[var(--text-2)]" />
                  <span className="text-sm text-[var(--text-2)]">Monthly Limit</span>
                </div>
                <span className="text-sm font-medium text-[var(--text-1)]">
                  ${limits.monthly_usage.toFixed(2)} / ${limits.monthly_limit.toFixed(2)}
                </span>
              </div>
              <div className="relative h-2 bg-[rgba(var(--glass-rgb),0.1)] rounded-full overflow-hidden">
                <motion.div
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{ 
                    backgroundColor: getUsageColor(getUsagePercentage(limits.monthly_usage, limits.monthly_limit))
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${getUsagePercentage(limits.monthly_usage, limits.monthly_limit)}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
              </div>
            </div>
          )}

          {/* Category Limits */}
          {limits?.category_limits && Object.keys(limits.category_limits).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-[var(--text-1)] mb-4">
                Category Limits
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(limits.category_limits).map(([category, info]) => {
                  const categoryConfig = SPENDING_CATEGORIES.find(c => c.value === category);
                  const percentage = getUsagePercentage(info.usage, info.limit);
                  
                  return (
                    <div key={category} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{categoryConfig?.icon || '💳'}</span>
                          <span className="text-sm text-[var(--text-2)] capitalize">
                            {categoryConfig?.label || category}
                          </span>
                        </div>
                        <span className="text-xs font-medium text-[var(--text-1)]">
                          ${info.usage.toFixed(0)} / ${info.limit.toFixed(0)}
                        </span>
                      </div>
                      <div className="relative h-1.5 bg-[rgba(var(--glass-rgb),0.1)] rounded-full overflow-hidden">
                        <motion.div
                          className="absolute inset-y-0 left-0 rounded-full"
                          style={{ 
                            backgroundColor: categoryConfig?.color || getUsageColor(percentage)
                          }}
                          initial={{ width: 0 }}
                          animate={{ width: `${percentage}%` }}
                          transition={{ duration: 0.5, ease: 'easeOut' }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {!limits?.daily_limit && !limits?.monthly_limit && (!limits?.category_limits || Object.keys(limits.category_limits).length === 0) && (
            <div className="text-center py-8">
              <ShoppingBag className="w-12 h-12 mx-auto mb-3 text-[var(--text-2)] opacity-50" />
              <p className="text-[var(--text-2)]">
                No spending limits set
              </p>
              <p className="text-sm text-[var(--text-2)] mt-1">
                Set limits to control your spending
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Edit Limits Modal */}
      <Modal
        isOpen={isEditing}
        onClose={() => setIsEditing(false)}
        title="Edit Spending Limits"
        size="md"
      >
        <div className="space-y-6">
          {/* Daily Limit */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
              Daily Limit
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--text-2)]" />
              <input
                type="number"
                value={dailyLimit}
                onChange={(e) => setDailyLimit(e.target.value)}
                placeholder="0.00"
                className="w-full pl-10 px-3 py-2 bg-[rgba(var(--glass-rgb),0.1)] border border-[rgba(var(--glass-rgb),0.2)] rounded-lg focus:outline-none focus:border-[var(--primary-blue)] transition-colors"
              />
            </div>
          </div>

          {/* Monthly Limit */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
              Monthly Limit
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--text-2)]" />
              <input
                type="number"
                value={monthlyLimit}
                onChange={(e) => setMonthlyLimit(e.target.value)}
                placeholder="0.00"
                className="w-full pl-10 px-3 py-2 bg-[rgba(var(--glass-rgb),0.1)] border border-[rgba(var(--glass-rgb),0.2)] rounded-lg focus:outline-none focus:border-[var(--primary-blue)] transition-colors"
              />
            </div>
          </div>

          {/* Category Limits */}
          <div>
            <h4 className="text-sm font-medium text-[var(--text-1)] mb-3">
              Category Limits
            </h4>
            <div className="space-y-3">
              {SPENDING_CATEGORIES.map((category) => (
                <div key={category.value} className="flex items-center gap-3">
                  <span className="text-lg w-8">{category.icon}</span>
                  <span className="text-sm text-[var(--text-2)] flex-1">
                    {category.label}
                  </span>
                  <div className="relative w-32">
                    <DollarSign className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3 h-3 text-[var(--text-2)]" />
                    <input
                      type="number"
                      value={categoryLimits[category.value] || ''}
                      onChange={(e) => setCategoryLimits({
                        ...categoryLimits,
                        [category.value]: e.target.value
                      })}
                      placeholder="0"
                      className="w-full pl-7 pr-2 py-1.5 text-sm bg-[rgba(var(--glass-rgb),0.1)] border border-[rgba(var(--glass-rgb),0.2)] rounded focus:outline-none focus:border-[var(--primary-blue)] transition-colors"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => setIsEditing(false)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              isLoading={isSaving}
              icon={<Check size={18} />}
            >
              Save Limits
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}