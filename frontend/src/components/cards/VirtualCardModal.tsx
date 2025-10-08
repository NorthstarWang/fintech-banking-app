'use client';

import { useState, useCallback, memo } from 'react';
import { motion } from 'framer-motion';
import {
  CreditCard,
  DollarSign,
  Calendar,
  ShoppingBag,
  Shield,
  Check,
  Info,
  Globe,
  Package
} from 'lucide-react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Dropdown from '@/components/ui/Dropdown';
import { cardsApi } from '@/lib/api';
import type { VirtualCardCreate, Account } from '@/lib/api';

interface VirtualCardModalProps {
  isOpen: boolean;
  onClose: () => void;
  parentCardId?: number;
  accounts?: Account[];
  onSuccess?: () => void;
}

const MERCHANT_CATEGORIES = [
  { value: 'all', label: 'All Merchants', icon: <Globe className="w-4 h-4" /> },
  { value: 'online', label: 'Online Shopping', icon: <ShoppingBag className="w-4 h-4" /> },
  { value: 'subscription', label: 'Subscriptions', icon: <Package className="w-4 h-4" /> },
  { value: 'travel', label: 'Travel', icon: <Globe className="w-4 h-4" /> },
];

const VirtualCardModal = memo(({
  isOpen,
  onClose,
  parentCardId,
  accounts = [],
  onSuccess
}: VirtualCardModalProps) => {
  const [step, setStep] = useState(1);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form data
  const [formData, setFormData] = useState<VirtualCardCreate>({
    account_id: 0,
    spending_limit: undefined,
    merchant_restrictions: [],
    expires_in_days: 30,
    single_use: false,
    name: ''
  });

  const handleCreate = async () => {
    try {
      setIsCreating(true);
      setError(null);

      if (!parentCardId && !formData.account_id) {
        setError('Please select an account');
        return;
      }

      let _response;
      if (parentCardId) {
        _response = await cardsApi.createVirtualCardFromParent(parentCardId, formData);
      } else {
        _response = await cardsApi.createVirtualCard(formData);
      }

      onSuccess?.();
      handleClose();
    } catch {
      setError('Failed to create virtual card');
    } finally {
      setIsCreating(false);
    }
  };

  const handleClose = useCallback(() => {
    setStep(1);
    setFormData({
      account_id: 0,
      spending_limit: undefined,
      merchant_restrictions: [],
      expires_in_days: 30,
      single_use: false,
      name: ''
    });
    setError(null);
    onClose();
  }, [onClose]);

  const toggleMerchantRestriction = useCallback((category: string) => {
    setFormData(prev => ({
      ...prev,
      merchant_restrictions: prev.merchant_restrictions?.includes(category)
        ? prev.merchant_restrictions.filter(c => c !== category)
        : [...(prev.merchant_restrictions || []), category]
    }));
  }, []);

  // Optimized input handlers
  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, name: e.target.value }));
  }, []);

  const handleAccountChange = useCallback((value: string) => {
    setFormData(prev => ({ ...prev, account_id: parseInt(value) }));
  }, []);

  const handleSpendingLimitChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ 
      ...prev, 
      spending_limit: e.target.value ? parseFloat(e.target.value) : undefined 
    }));
  }, []);

  const handleExpiryDaysChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ 
      ...prev, 
      expires_in_days: parseInt(e.target.value) || 30 
    }));
  }, []);

  const handleSingleUseChange = useCallback((single_use: boolean) => {
    setFormData(prev => ({ ...prev, single_use }));
  }, []);

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create Virtual Card"
      size="md"
    >
      <div className="space-y-6">
        {/* Progress Steps */}
        <div className="flex items-center justify-between mb-6">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`flex items-center ${s < 3 ? 'flex-1' : ''}`}
            >
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  ${step >= s 
                    ? 'bg-[var(--primary-blue)] text-white' 
                    : 'bg-[rgba(var(--glass-rgb),0.1)] text-[var(--text-2)]'
                  }
                `}
              >
                {step > s ? <Check className="w-4 h-4" /> : s}
              </div>
              {s < 3 && (
                <div
                  className={`
                    flex-1 h-1 mx-2
                    ${step > s 
                      ? 'bg-[var(--primary-blue)]' 
                      : 'bg-[rgba(var(--glass-rgb),0.1)]'
                    }
                  `}
                />
              )}
            </div>
          ))}
        </div>

        {error && (
          <div className="p-3 bg-[var(--error-bg)] border border-[var(--error-border)] rounded-lg">
            <p className="text-sm text-[var(--error-text)]">{error}</p>
          </div>
        )}

        {/* Step 1: Basic Info */}
        {step === 1 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <h3 className="text-lg font-semibold text-[var(--text-1)] mb-4">
              Card Details
            </h3>
            
            <div className="space-y-4">
              {!parentCardId && (
                <div>
                  <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                    Select Account
                  </label>
                  <Dropdown
                    value={formData.account_id.toString()}
                    onChange={handleAccountChange}
                    items={[
                      { value: '0', label: 'Select an account' },
                      ...accounts.map((account) => ({
                        value: account.id.toString(),
                        label: `${account.name} - $${account.balance.toFixed(2)}`
                      }))
                    ]}
                    fullWidth
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                  Card Name (Optional)
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={handleNameChange}
                  placeholder="e.g., Online Shopping"
                  className="w-full px-3 py-2 bg-[rgba(var(--glass-rgb),0.1)] border border-[rgba(var(--glass-rgb),0.2)] rounded-lg focus:outline-none focus:border-[var(--primary-blue)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                  Card Type
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <Card
                    variant={!formData.single_use ? 'subtle' : 'default'}
                    className={`p-4 cursor-pointer transition-all ${
                      !formData.single_use ? 'ring-2 ring-[var(--primary-blue)]' : ''
                    }`}
                    onClick={() => handleSingleUseChange(false)}
                  >
                    <CreditCard className="w-6 h-6 mb-2 text-[var(--primary-blue)]" />
                    <h4 className="font-medium text-[var(--text-1)]">Multi-use</h4>
                    <p className="text-xs text-[var(--text-2)] mt-1">
                      Use multiple times until expiry
                    </p>
                  </Card>
                  
                  <Card
                    variant={formData.single_use ? 'subtle' : 'default'}
                    className={`p-4 cursor-pointer transition-all ${
                      formData.single_use ? 'ring-2 ring-[var(--primary-blue)]' : ''
                    }`}
                    onClick={() => handleSingleUseChange(true)}
                  >
                    <Shield className="w-6 h-6 mb-2 text-[var(--primary-emerald)]" />
                    <h4 className="font-medium text-[var(--text-1)]">Single-use</h4>
                    <p className="text-xs text-[var(--text-2)] mt-1">
                      Expires after one transaction
                    </p>
                  </Card>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Step 2: Limits & Restrictions */}
        {step === 2 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <h3 className="text-lg font-semibold text-[var(--text-1)] mb-4">
              Limits & Restrictions
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                  Spending Limit
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--text-2)]" />
                  <input
                    type="number"
                    value={formData.spending_limit || ''}
                    onChange={handleSpendingLimitChange}
                    placeholder="No limit"
                    className="w-full pl-10 px-3 py-2 bg-[rgba(var(--glass-rgb),0.1)] border border-[rgba(var(--glass-rgb),0.2)] rounded-lg focus:outline-none focus:border-[var(--primary-blue)]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                  Validity Period
                </label>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-[var(--text-2)]" />
                  <input
                    type="number"
                    value={formData.expires_in_days}
                    onChange={handleExpiryDaysChange}
                    min="1"
                    max="365"
                    className="w-20 px-2 py-1 bg-[rgba(var(--glass-rgb),0.1)] border border-[rgba(var(--glass-rgb),0.2)] rounded focus:outline-none focus:border-[var(--primary-blue)]"
                  />
                  <span className="text-sm text-[var(--text-2)]">days</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                  Merchant Restrictions
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {MERCHANT_CATEGORIES.map((category) => (
                    <button
                      key={category.value}
                      onClick={() => toggleMerchantRestriction(category.value)}
                      className={`
                        p-3 rounded-lg border transition-all flex items-center gap-2
                        ${formData.merchant_restrictions?.includes(category.value)
                          ? 'bg-[rgba(var(--primary-blue),0.1)] border-[var(--primary-blue)] text-[var(--primary-blue)]'
                          : 'bg-[rgba(var(--glass-rgb),0.05)] border-[rgba(var(--glass-rgb),0.2)] text-[var(--text-2)]'
                        }
                      `}
                    >
                      {category.icon}
                      <span className="text-sm">{category.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Step 3: Review */}
        {step === 3 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <h3 className="text-lg font-semibold text-[var(--text-1)] mb-4">
              Review & Confirm
            </h3>
            
            <Card variant="subtle" className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-2)]">Card Name</span>
                <span className="text-sm font-medium text-[var(--text-1)]">
                  {formData.name || 'Virtual Card'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-2)]">Type</span>
                <span className="text-sm font-medium text-[var(--text-1)]">
                  {formData.single_use ? 'Single-use' : 'Multi-use'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-2)]">Spending Limit</span>
                <span className="text-sm font-medium text-[var(--text-1)]">
                  {formData.spending_limit ? `$${formData.spending_limit}` : 'No limit'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-2)]">Valid For</span>
                <span className="text-sm font-medium text-[var(--text-1)]">
                  {formData.expires_in_days} days
                </span>
              </div>
              
              {formData.merchant_restrictions && formData.merchant_restrictions.length > 0 && (
                <div>
                  <span className="text-sm text-[var(--text-2)]">Restrictions</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {formData.merchant_restrictions.map((restriction) => (
                      <span
                        key={restriction}
                        className="px-2 py-1 bg-[rgba(var(--glass-rgb),0.1)] rounded text-xs text-[var(--text-1)]"
                      >
                        {MERCHANT_CATEGORIES.find(c => c.value === restriction)?.label || restriction}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </Card>

            <div className="mt-4 p-3 bg-[rgba(var(--glass-rgb),0.05)] rounded-lg">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-[var(--primary-blue)] mt-0.5" />
                <p className="text-xs text-[var(--text-2)]">
                  Your virtual card will be created instantly and ready to use for online purchases.
                  Card details will be available in your cards list.
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Actions */}
        <div className="flex justify-between pt-4">
          {step > 1 ? (
            <Button
              variant="secondary"
              onClick={() => setStep(step - 1)}
              disabled={isCreating}
            >
              Back
            </Button>
          ) : (
            <Button
              variant="secondary"
              onClick={handleClose}
              disabled={isCreating}
            >
              Cancel
            </Button>
          )}
          
          {step < 3 ? (
            <Button
              variant="primary"
              onClick={() => setStep(step + 1)}
              disabled={step === 1 && !parentCardId && !formData.account_id}
            >
              Next
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={handleCreate}
              isLoading={isCreating}
              icon={<Check size={18} />}
            >
              Create Card
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
});

VirtualCardModal.displayName = 'VirtualCardModal';

export default VirtualCardModal;