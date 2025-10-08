import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { 
  Send, 
  Plus, 
  ArrowRightLeft, 
  QrCode,
  Receipt,
  CreditCard,
  Target,
  FileText
} from 'lucide-react';
import TransferModal from '../modals/TransferModal';
import DepositModal from '../modals/DepositModal';
import BillPaymentModal from '../modals/BillPaymentModal';
import QRScannerModal from '../ui/QRScannerModal';
import { useAlert } from '@/contexts/AlertContext';

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  onClick: () => void;
}

interface QuickActionsProps {
  analyticsId?: string;
  analyticsLabel?: string;
  onActionComplete?: () => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  analyticsId: _analyticsId = 'quick-actions',
  analyticsLabel: _analyticsLabel = 'Quick Actions',
  onActionComplete,
}) => {
  const router = useRouter();
  const { showSuccess } = useAlert();
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showSendMoneyModal, setShowSendMoneyModal] = useState(false);
  const [showBillPaymentModal, setShowBillPaymentModal] = useState(false);
  const [showQRScannerModal, setShowQRScannerModal] = useState(false);
  const actions: QuickAction[] = [
    {
      id: 'send',
      label: 'Send Money',
      icon: <Send size={20} />,
      color: 'from-[var(--primary-blue)] to-[var(--primary-indigo)]',
      onClick: () => {
        setShowSendMoneyModal(true);
      },
    },
    {
      id: 'add',
      label: 'Add Money',
      icon: <Plus size={20} />,
      color: 'from-[var(--primary-emerald)] to-[var(--primary-teal)]',
      onClick: () => {
        setShowDepositModal(true);
      },
    },
    {
      id: 'transfer',
      label: 'Transfer',
      icon: <ArrowRightLeft size={20} />,
      color: 'from-[var(--primary-indigo)] to-[var(--primary-navy)]',
      onClick: () => {
        setShowTransferModal(true);
      },
    },
    {
      id: 'scan',
      label: 'Scan QR',
      icon: <QrCode size={20} />,
      color: 'from-[var(--primary-teal)] to-[var(--primary-blue)]',
      onClick: () => {
        setShowQRScannerModal(true);
      },
    },
    {
      id: 'bills',
      label: 'Pay Bills',
      icon: <Receipt size={20} />,
      color: 'from-[var(--primary-blue)] to-[var(--primary-teal)]',
      onClick: () => {
        setShowBillPaymentModal(true);
      },
    },
    {
      id: 'cards',
      label: 'My Cards',
      icon: <CreditCard size={20} />,
      color: 'from-[var(--primary-indigo)] to-[var(--primary-blue)]',
      onClick: () => {
        router.push('/cards');
      },
    },
    {
      id: 'goals',
      label: 'Goals',
      icon: <Target size={20} />,
      color: 'from-[var(--primary-emerald)] to-[var(--primary-green)]',
      onClick: () => {
        router.push('/budget');
      },
    },
    {
      id: 'statements',
      label: 'Statements',
      icon: <FileText size={20} />,
      color: 'from-[var(--primary-navy)] to-[var(--primary-indigo)]',
      onClick: () => {
        router.push('/transactions');
      },
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.8 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.3,
      },
    },
  };

  return (
    <div>
      <h2 className="text-xl font-semibold text-[var(--text-1)] mb-4">
        Quick Actions
      </h2>
      
      <motion.div
        className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 sm:gap-4"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {actions.map((action) => (
          <motion.div
            key={action.id}
            variants={itemVariants}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <button
              onClick={action.onClick}
              className={`
                w-full p-3 sm:p-4 rounded-xl 
                bg-[rgba(var(--glass-rgb),0.3)] backdrop-blur-sm 
                border border-[var(--glass-border)] 
                hover:bg-[rgba(var(--glass-rgb),0.4)] 
                hover:border-[var(--glass-border-prominent)] 
                transition-all duration-200 group
                touch-manipulation tap-highlight-transparent
                ${action.id === 'send' ? 'quick-action-send' : ''}
              `}
            >
              <div className="flex flex-col items-center gap-2 sm:gap-3">
                <div className={`
                  w-10 h-10 sm:w-12 sm:h-12 rounded-xl
                  bg-gradient-to-br ${action.color}
                  flex items-center justify-center
                  text-white shadow-lg
                  group-hover:shadow-xl
                  transition-shadow duration-200
                `}>
                  {action.icon}
                </div>
                <span className="text-xs font-medium text-[var(--text-1)] text-center">
                  {action.label}
                </span>
              </div>
            </button>
          </motion.div>
        ))}
      </motion.div>

      {/* Modals */}
      {showTransferModal && (
        <TransferModal
          isOpen={showTransferModal}
          onClose={() => {
            setShowTransferModal(false);
            if (onActionComplete) {
              onActionComplete();
            }
          }}
        />
      )}

      {showDepositModal && (
        <DepositModal
          isOpen={showDepositModal}
          onClose={() => {
            setShowDepositModal(false);
            if (onActionComplete) {
              onActionComplete();
            }
          }}
        />
      )}

      {showSendMoneyModal && (
        <TransferModal
          isOpen={showSendMoneyModal}
          onClose={() => {
            setShowSendMoneyModal(false);
            if (onActionComplete) {
              onActionComplete();
            }
          }}
          isExternal={true}
        />
      )}

      {showBillPaymentModal && (
        <BillPaymentModal
          isOpen={showBillPaymentModal}
          onClose={() => {
            setShowBillPaymentModal(false);
            if (onActionComplete) {
              onActionComplete();
            }
          }}
        />
      )}

      {showQRScannerModal && (
        <QRScannerModal
          isOpen={showQRScannerModal}
          onClose={() => {
            setShowQRScannerModal(false);
            if (onActionComplete) {
              onActionComplete();
            }
          }}
          onScanSuccess={(_data) => {
            showSuccess('Payment Processed', 'QR code payment has been processed successfully');
            // Handle the scanned data as needed
          }}
        />
      )}
    </div>
  );
};

export default QuickActions;
