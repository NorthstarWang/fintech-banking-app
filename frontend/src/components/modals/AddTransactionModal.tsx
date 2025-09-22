import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  X, 
  Calendar, 
  DollarSign, 
  Tag, 
  FileText,
  CreditCard,
  Building,
  AlertCircle
} from 'lucide-react';
import Modal from '../ui/Modal';
import Input from '../ui/Input';
import Button from '../ui/Button';
import Dropdown from '../ui/Dropdown';
import DatePicker from '../ui/DatePicker';
import { 
  transactionsService, 
  accountsService,
  categoriesService,
  TransactionCreate,
  Account,
  Category
} from '@/lib/api';

interface AddTransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AddTransactionModal: React.FC<AddTransactionModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<TransactionCreate>({
    account_id: 0,
    amount: 0,
    transaction_type: 'DEBIT',
    description: '',
    merchant_name: '',
    transaction_date: new Date().toISOString().split('T')[0],
  });
  
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen) {
      loadAccountsAndCategories();
    }
  }, [isOpen]);

  const loadAccountsAndCategories = async () => {
    try {
      const [accountsData, categoriesData] = await Promise.all([
        accountsService.getAccounts(),
        categoriesService.getCategories()
      ]);
      setAccounts(accountsData);
      setCategories(categoriesData);
      
      // Set default account if available
      if (accountsData.length > 0 && !formData.account_id) {
        setFormData(prev => ({ ...prev, account_id: accountsData[0].id }));
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.account_id) {
      newErrors.account_id = 'Please select an account';
    }

    if (!formData.amount || formData.amount <= 0) {
      newErrors.amount = 'Please enter a valid amount';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Please enter a description';
    }

    if (!formData.transaction_date) {
      newErrors.transaction_date = 'Please select a date';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      await transactionsService.createTransaction(formData);
      
        text: 'Transaction created successfully',
        custom_action: 'add_transaction',
        data: {
          transaction_type: formData.transaction_type,
          amount: formData.amount,
          category_id: formData.category_id
        }
      });

      onSuccess();
      onClose();
      
      // Reset form
      setFormData({
        account_id: accounts[0]?.id || 0,
        amount: 0,
        transaction_type: 'DEBIT',
        description: '',
        merchant_name: '',
        transaction_date: new Date().toISOString().split('T')[0],
      });
      setErrors({});
    } catch (error) {
      console.error('Failed to create transaction:', error);
      setErrors({ submit: 'Failed to create transaction. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const transactionTypes = [
    { value: 'DEBIT', label: 'Expense (Debit)' },
    { value: 'CREDIT', label: 'Income (Credit)' }
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Transaction"
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {errors.submit && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-[rgba(var(--primary-red),0.1)] text-[var(--primary-red)]">
            <AlertCircle className="w-5 h-5" />
            <p className="text-sm">{errors.submit}</p>
          </div>
        )}

        {/* Transaction Type */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-2)] mb-2">
            Transaction Type
          </label>
          <Dropdown
            items={transactionTypes}
            value={formData.transaction_type}
            onChange={(value) => setFormData({ ...formData, transaction_type: value as 'DEBIT' | 'CREDIT' })}
            placeholder="Select type"
          />
        </div>

        {/* Amount */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-2)] mb-2">
            Amount
          </label>
          <Input
            type="number"
            value={formData.amount || ''}
            onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })}
            placeholder="0.00"
            icon={<DollarSign size={18} />}
            error={errors.amount}
            step="0.01"
            min="0"
          />
        </div>

        {/* Account */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-2)] mb-2">
            Account
          </label>
          <Dropdown
            items={accounts.map(account => ({
              value: account.id.toString(),
              label: `${account.name} (${account.account_type})`
            }))}
            value={formData.account_id.toString()}
            onChange={(value) => setFormData({ ...formData, account_id: parseInt(value) })}
            placeholder="Select account"
            icon={<CreditCard size={18} />}
          />
          {errors.account_id && (
            <p className="mt-1 text-sm text-[var(--primary-red)]">{errors.account_id}</p>
          )}
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-2)] mb-2">
            Category
          </label>
          <Dropdown
            items={[
              { value: '', label: 'No category' },
              ...categories.map(category => ({
                value: category.id.toString(),
                label: category.name
              }))
            ]}
            value={formData.category_id?.toString() || ''}
            onChange={(value) => setFormData({ 
              ...formData, 
              category_id: value ? parseInt(value) : undefined 
            })}
            placeholder="Select category"
            icon={<Tag size={18} />}
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-2)] mb-2">
            Description
          </label>
          <Input
            type="text"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Enter transaction description"
            icon={<FileText size={18} />}
            error={errors.description}
          />
        </div>

        {/* Merchant */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-2)] mb-2">
            Merchant (Optional)
          </label>
          <Input
            type="text"
            value={formData.merchant_name || ''}
            onChange={(e) => setFormData({ ...formData, merchant_name: e.target.value })}
            placeholder="Enter merchant name"
            icon={<Building size={18} />}
          />
        </div>

        {/* Date */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-2)] mb-2">
            Date
          </label>
          <DatePicker
            value={formData.transaction_date || new Date().toISOString().split('T')[0]}
            onChange={(date) => setFormData({ ...formData, transaction_date: date })}
            error={errors.transaction_date}
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4">
          <Button
            type="button"
            variant="secondary"
            fullWidth
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            fullWidth
            disabled={isLoading}
          >
            {isLoading ? 'Adding...' : 'Add Transaction'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default AddTransactionModal;
