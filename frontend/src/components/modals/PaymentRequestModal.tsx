'use client';

import { useState } from 'react';
import {
  DollarSign,
  Calendar,
  MessageSquare,
  Send,
  User
} from 'lucide-react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { p2pApi, P2PContact } from '@/lib/api/p2p';

interface PaymentRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  contacts: P2PContact[];
  onSuccess?: () => void;
}

export default function PaymentRequestModal({
  isOpen,
  onClose,
  contacts,
  onSuccess
}: PaymentRequestModalProps) {
  const [selectedContact, setSelectedContact] = useState<P2PContact | null>(null);
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [showContactList, setShowContactList] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSubmit = async () => {
    if (!selectedContact || !amount || !description) {
      setError('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      await p2pApi.createPaymentRequest({
        requester_id: selectedContact.id,
        amount: parseFloat(amount),
        description: description,
        due_date: dueDate || undefined
      });

      onSuccess?.();
      handleClose();
    } catch {
      setError('Failed to create payment request');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setSelectedContact(null);
    setAmount('');
    setDescription('');
    setDueDate('');
    setError('');
    setShowContactList(false);
    setSearchQuery('');
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Request Payment"
      size="md"
    >
      <div className="space-y-4">
        {/* Contact Selection */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
            Request From
          </label>
          
          {!selectedContact ? (
            <div>
              <Input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setShowContactList(true);
                }}
                onFocus={() => setShowContactList(true)}
                placeholder="Search contacts..."
                icon={<User size={18} />}
              />
              
              {showContactList && (
                <div className="mt-2 max-h-48 overflow-y-auto rounded-lg border border-[var(--border-1)] bg-[var(--bg-1)]">
                  {filteredContacts.map(contact => (
                    <button
                      key={contact.id}
                      onClick={() => {
                        setSelectedContact(contact);
                        setShowContactList(false);
                        setSearchQuery('');
                      }}
                      className="w-full p-3 hover:bg-[rgba(var(--glass-rgb),0.1)] flex items-center gap-3 transition-all"
                    >
                      <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[var(--primary-blue)] to-[var(--primary-indigo)] flex items-center justify-center text-white font-medium">
                        {contact.name.charAt(0)}
                      </div>
                      <div className="text-left">
                        <p className="font-medium text-[var(--text-1)]">{contact.name}</p>
                        <p className="text-sm text-[var(--text-2)]">{contact.username}</p>
                      </div>
                    </button>
                  ))}
                  
                  {filteredContacts.length === 0 && (
                    <p className="text-center py-4 text-[var(--text-2)]">
                      No contacts found
                    </p>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-between p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[var(--primary-blue)] to-[var(--primary-indigo)] flex items-center justify-center text-white font-medium">
                  {selectedContact.name.charAt(0)}
                </div>
                <div>
                  <p className="font-medium text-[var(--text-1)]">{selectedContact.name}</p>
                  <p className="text-sm text-[var(--text-2)]">{selectedContact.username}</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedContact(null)}
              >
                Change
              </Button>
            </div>
          )}
        </div>

        {/* Amount */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
            Amount
          </label>
          <Input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            icon={<DollarSign size={18} />}
            size="lg"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
            Description
          </label>
          <Input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What's this payment for?"
            icon={<MessageSquare size={18} />}
          />
        </div>

        {/* Due Date (Optional) */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
            Due Date (Optional)
          </label>
          <Input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            icon={<Calendar size={18} />}
            min={new Date().toISOString().split('T')[0]}
          />
        </div>

        {/* Preview */}
        {selectedContact && amount && (
          <div className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)]">
            <h4 className="text-sm font-medium text-[var(--text-1)] mb-3">Request Preview</h4>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-[var(--text-2)]">Requesting from</span>
                <span className="text-[var(--text-1)]">{selectedContact.name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[var(--text-2)]">Amount</span>
                <span className="text-[var(--text-1)] font-medium">
                  ${parseFloat(amount).toFixed(2)}
                </span>
              </div>
              {dueDate && (
                <div className="flex justify-between text-sm">
                  <span className="text-[var(--text-2)]">Due by</span>
                  <span className="text-[var(--text-1)]">
                    {new Date(dueDate).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-3 rounded-lg bg-[rgba(var(--primary-red),0.1)] text-[var(--primary-red)] text-sm">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="secondary"
            fullWidth
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            fullWidth
            onClick={handleSubmit}
            disabled={!selectedContact || !amount || !description || isSubmitting}
            loading={isSubmitting}
            icon={<Send size={18} />}
          >
            Send Request
          </Button>
        </div>
      </div>
    </Modal>
  );
}