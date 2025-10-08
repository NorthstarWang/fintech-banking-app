import React from 'react';
import { AlertTriangle } from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import { accountsService } from '@/lib/api';
import { useAlert } from '@/contexts/AlertContext';

interface DeleteAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  account: {
    id: string;
    name: string;
    balance: number;
  };
  onAccountDeleted: () => void;
}

export default function DeleteAccountModal({
  isOpen,
  onClose,
  account,
  onAccountDeleted,
}: DeleteAccountModalProps) {
  const [isDeleting, setIsDeleting] = React.useState(false);
  const { showSuccess, showError } = useAlert();

  const handleDelete = async () => {
    try {
      setIsDeleting(true);
      await accountsService.deleteAccount(parseInt(account.id));
      
      showSuccess('Account Deleted', `${account.name} has been deleted successfully.`);
      
      onAccountDeleted();
      onClose();
    } catch (error) {
      showError('Delete Failed', error instanceof Error ? error.message : 'Failed to delete account. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Account"
      className="max-w-md"
    >
      <div className="space-y-6">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-full bg-[rgba(var(--primary-red-rgb),0.1)]">
            <AlertTriangle className="w-6 h-6 text-[var(--primary-red)]" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-[var(--text-1)] mb-2">
              Are you sure?
            </h3>
            <p className="text-[var(--text-2)] mb-4">
              You&apos;re about to delete the account <span className="font-semibold">&quot;{account.name}&quot;</span>.
              This action cannot be undone.
            </p>
            {account.balance !== 0 && (
              <div className="p-3 rounded-lg bg-[rgba(var(--primary-yellow-rgb),0.1)] border border-[rgba(var(--primary-yellow-rgb),0.2)]">
                <p className="text-sm text-[var(--primary-yellow)]">
                  ⚠️ This account has a balance of ${Math.abs(account.balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}.
                  Make sure to transfer or withdraw funds before deleting.
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border-1)]">
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleDelete}
            disabled={isDeleting}
            loading={isDeleting}
          >
            Delete Account
          </Button>
        </div>
      </div>
    </Modal>
  );
}