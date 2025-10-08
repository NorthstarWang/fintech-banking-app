'use client';

import React, { useState, useCallback, memo } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { CreditCard } from 'lucide-react';
import { cardsApi } from '@/lib/api';
import { notificationService } from '@/services/notificationService';
import type { Account } from '@/lib/api';

interface AddCardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  accounts: Account[];
}

interface NewCardData {
  card_number: string;
  card_type: 'credit' | 'debit';
  card_name: string;
  credit_limit?: number;
  linked_account_id?: number;
}

const AddCardModal = memo(({ isOpen, onClose, onSuccess, accounts }: AddCardModalProps) => {
  const [isAddingCard, setIsAddingCard] = useState(false);
  const [newCardData, setNewCardData] = useState<NewCardData>({
    card_number: '',
    card_type: 'credit',
    card_name: '',
    credit_limit: 5000,
  });

  const handleClose = useCallback(() => {
    setNewCardData({
      card_number: '',
      card_type: 'credit',
      card_name: '',
      credit_limit: 5000,
    });
    onClose();
  }, [onClose]);

  const handleCardTypeChange = useCallback((value: string) => {
    setNewCardData(prev => ({ ...prev, card_type: value as 'credit' | 'debit' }));
  }, []);

  const handleCardNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setNewCardData(prev => ({ ...prev, card_name: e.target.value }));
  }, []);

  const handleCardNumberChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\s/g, '');
    if (value.length <= 16 && /^\d*$/.test(value)) {
      setNewCardData(prev => ({ ...prev, card_number: value }));
    }
  }, []);

  const handleCreditLimitChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setNewCardData(prev => ({ ...prev, credit_limit: parseFloat(e.target.value) || 0 }));
  }, []);

  const handleAccountChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setNewCardData(prev => ({ ...prev, linked_account_id: parseInt(e.target.value) || undefined }));
  }, []);

  const handleAddCard = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAddingCard(true);
    
    try {
      const cardDataToSubmit: any = {
        card_number: newCardData.card_number,
        card_type: newCardData.card_type,
        card_name: newCardData.card_name,
        issuer: 'Bank',
        expiry_date: '12/27',
        billing_cycle_day: 15,
        interest_rate: 19.99,
      };

      if (newCardData.card_type === 'credit') {
        cardDataToSubmit.credit_limit = newCardData.credit_limit;
        cardDataToSubmit.current_balance = 0;
      } else {
        cardDataToSubmit.linked_account_id = newCardData.linked_account_id;
      }

      await cardsApi.createCard(cardDataToSubmit);
      notificationService.success('Card added successfully!');
      handleClose();
      onSuccess();
    } catch {
      notificationService.error('Failed to add card. Please try again.');
    } finally {
      setIsAddingCard(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Add New Card"
      icon={<CreditCard className="text-[var(--primary-blue)]" />}
    >
      <form onSubmit={handleAddCard} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-[var(--text-1)] mb-1">
            Card Type
          </label>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => handleCardTypeChange('credit')}
              className={`flex-1 px-4 py-2 rounded-lg border transition-all ${
                newCardData.card_type === 'credit'
                  ? 'bg-[var(--primary-blue)] border-[var(--primary-blue)] text-white'
                  : 'bg-transparent border-[var(--border-1)] text-[var(--text-2)]'
              }`}
            >
              Credit
            </button>
            <button
              type="button"
              onClick={() => handleCardTypeChange('debit')}
              className={`flex-1 px-4 py-2 rounded-lg border transition-all ${
                newCardData.card_type === 'debit'
                  ? 'bg-[var(--primary-blue)] border-[var(--primary-blue)] text-white'
                  : 'bg-transparent border-[var(--border-1)] text-[var(--text-2)]'
              }`}
            >
              Debit
            </button>
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-[var(--text-1)] mb-1">
            Card Name
          </label>
          <input
            type="text"
            value={newCardData.card_name}
            onChange={handleCardNameChange}
            className="w-full px-3 py-2 bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)] rounded-lg text-[var(--text-1)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)] focus:border-transparent"
            placeholder="e.g., Platinum Rewards"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-[var(--text-1)] mb-1">
            Card Number
          </label>
          <input
            type="text"
            value={newCardData.card_number}
            onChange={handleCardNumberChange}
            className="w-full px-3 py-2 bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)] rounded-lg text-[var(--text-1)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)] focus:border-transparent font-mono"
            placeholder="1234567890123456"
            maxLength={16}
            required
          />
        </div>
        
        {newCardData.card_type === 'credit' && (
          <div>
            <label className="block text-sm font-medium text-[var(--text-1)] mb-1">
              Credit Limit
            </label>
            <input
              type="number"
              value={newCardData.credit_limit || ''}
              onChange={handleCreditLimitChange}
              className="w-full px-3 py-2 bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)] rounded-lg text-[var(--text-1)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)] focus:border-transparent"
              placeholder="5000"
              min="0"
              step="100"
              required
            />
          </div>
        )}
        
        {newCardData.card_type === 'debit' && (
          <div>
            <label className="block text-sm font-medium text-[var(--text-1)] mb-1">
              Link to Account
            </label>
            <select
              value={newCardData.linked_account_id || ''}
              onChange={handleAccountChange}
              className="w-full px-3 py-2 bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)] rounded-lg text-[var(--text-1)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-blue)] focus:border-transparent"
              required
            >
              <option value="">Select an account</option>
              {accounts.filter(acc => acc.account_type === 'CHECKING' || acc.account_type === 'SAVINGS').map(account => (
                <option key={account.id} value={account.id}>
                  {account.name} ({account.account_type})
                </option>
              ))}
            </select>
          </div>
        )}
        
        <div className="flex justify-end gap-3 pt-4">
          <Button
            variant="secondary"
            onClick={handleClose}
            type="button"
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            disabled={isAddingCard}
          >
            {isAddingCard ? 'Adding...' : 'Add Card'}
          </Button>
        </div>
      </form>
    </Modal>
  );
});

AddCardModal.displayName = 'AddCardModal';

export default AddCardModal;