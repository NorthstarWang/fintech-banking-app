'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, AlertCircle, Snowflake, CreditCard } from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import Switch from '../ui/Switch';

interface FreezeCardModalProps {
  isOpen: boolean;
  onClose: () => void;
  card: {
    id: string;
    lastFour: string;
    status: 'active' | 'frozen';
    type: string;
  };
  onFreeze: (frozen: boolean) => void;
}

export const FreezeCardModal: React.FC<FreezeCardModalProps> = ({
  isOpen,
  onClose,
  card,
  onFreeze,
}) => {
  const [isFrozen, setIsFrozen] = useState(card.status === 'frozen');
  const [confirming, setConfirming] = useState(false);

  // Update the frozen state when the card prop changes
  useEffect(() => {
    setIsFrozen(card.status === 'frozen');
  }, [card.status]);

  const handleToggle = () => {
    if (!isFrozen) {
      // Show confirmation for freezing
      setConfirming(true);
    } else {
      // Unfreeze immediately
      handleConfirm();
    }
  };

  const handleConfirm = () => {
    const newStatus = !isFrozen;
    setIsFrozen(newStatus);
    setConfirming(false);

    onFreeze(newStatus);
    
    // Close modal after a short delay
    setTimeout(() => {
      onClose();
    }, 500);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Card Security"
      size="sm"
      analyticsId="freeze-card-modal"
      analyticsLabel="Freeze Card Modal"
    >
      <div className="space-y-6">
        {/* Card Info */}
        <div className="flex items-center gap-4 p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] border border-[var(--border-1)]">
          <div className="p-3 rounded-lg bg-gradient-to-br from-[var(--primary-blue)] to-[var(--primary-indigo)]">
            <CreditCard className="w-6 h-6 text-white" />
          </div>
          <div>
            <p className="font-medium text-[var(--text-1)]">
              {card.type} Card
            </p>
            <p className="text-sm text-[var(--text-2)]">
              •••• {card.lastFour}
            </p>
          </div>
        </div>

        {!confirming ? (
          <>
            {/* Freeze Toggle */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`
                    p-2 rounded-lg transition-colors
                    ${isFrozen 
                      ? 'bg-[var(--primary-blue)]/10 text-[var(--primary-blue)]' 
                      : 'bg-[rgba(var(--glass-rgb),0.1)] text-[var(--text-2)]'
                    }
                  `}>
                    <Snowflake className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-medium text-[var(--text-1)]">
                      {isFrozen ? 'Card is Frozen' : 'Freeze Card'}
                    </p>
                    <p className="text-sm text-[var(--text-2)]">
                      {isFrozen 
                        ? 'All transactions are blocked' 
                        : 'Temporarily block all transactions'
                      }
                    </p>
                  </div>
                </div>
                <Switch
                  checked={isFrozen}
                  onCheckedChange={handleToggle}
                />
              </div>

              {/* Info Message */}
              <div className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)]">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-[var(--primary-emerald)] mt-0.5" />
                  <div className="space-y-2">
                    <p className="text-sm text-[var(--text-2)]">
                      {isFrozen 
                        ? 'Your card is currently frozen. No transactions can be made until you unfreeze it.'
                        : 'Freezing your card will immediately block all transactions including:'
                      }
                    </p>
                    {!isFrozen && (
                      <ul className="text-sm text-[var(--text-2)] space-y-1 ml-4">
                        <li>• In-store purchases</li>
                        <li>• Online transactions</li>
                        <li>• ATM withdrawals</li>
                        <li>• Recurring payments</li>
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <Button
                variant="secondary"
                fullWidth
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button
                variant={isFrozen ? 'primary' : 'danger'}
                fullWidth
                onClick={handleToggle}
                icon={<Snowflake size={16} />}
              >
                {isFrozen ? 'Unfreeze Card' : 'Freeze Card'}
              </Button>
            </div>
          </>
        ) : (
          <>
            {/* Confirmation */}
            <div className="space-y-4">
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--primary-amber)]/10 flex items-center justify-center">
                  <AlertCircle className="w-8 h-8 text-[var(--primary-amber)]" />
                </div>
                <h3 className="text-lg font-semibold text-[var(--text-1)] mb-2">
                  Confirm Card Freeze
                </h3>
                <p className="text-[var(--text-2)]">
                  Are you sure you want to freeze your card ending in {card.lastFour}?
                </p>
              </div>

              <div className="p-4 rounded-lg bg-[var(--primary-amber)]/10 border border-[var(--primary-amber)]/20">
                <p className="text-sm text-[var(--primary-amber)]">
                  This action will immediately block all card transactions. You can unfreeze your card at any time.
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <Button
                variant="secondary"
                fullWidth
                onClick={() => setConfirming(false)}
              >
                Go Back
              </Button>
              <Button
                variant="danger"
                fullWidth
                onClick={handleConfirm}
                icon={<Snowflake size={16} />}
              >
                Freeze Card
              </Button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};

export default FreezeCardModal;
