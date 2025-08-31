'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send,
  UserPlus,
  Search,
  QrCode,
  DollarSign,
  Clock,
  CheckCircle,
  AlertCircle,
  ArrowUpRight,
  ArrowDownLeft,
  Users,
  Smartphone,
  Mail,
  MessageSquare,
  History,
  Filter,
  Plus,
  Star,
  User,
  Zap
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import Dropdown from '@/components/ui/Dropdown';
import SlideToConfirm from '@/components/ui/SlideToConfirm';
import P2PContactList from '@/components/p2p/P2PContactList';
import P2PTransactionHistory from '@/components/p2p/P2PTransactionHistory';
import P2PQuickSend from '@/components/p2p/P2PQuickSend';
import SplitPaymentModal from '@/components/modals/SplitPaymentModal';
import PaymentRequestModal from '@/components/modals/PaymentRequestModal';
import QRCodeModal from '@/components/modals/QRCodeModal';
import { p2pApi } from '@/lib/api/p2p';
import { accountsService } from '@/lib/api/accounts';
import { Account } from '@/lib/api/accounts';
import { useAuth } from '@/contexts/AuthContext';

export interface P2PContact {
  id: string;
  name: string;
  username: string;
  email: string;
  phone: string;
  avatar?: string;
  isFavorite: boolean;
  lastTransaction?: {
    date: string;
    amount: number;
    type: 'sent' | 'received';
  };
}

export interface P2PTransaction {
  id: string;
  contact: P2PContact;
  amount: number;
  type: 'sent' | 'received';
  status: 'completed' | 'pending' | 'failed';
  date: string;
  description: string;
  method: 'instant' | 'standard';
  fee?: number;
}

export default function P2PPage() {
  const { user } = useAuth();
  const [contacts, setContacts] = useState<P2PContact[]>([]);
  const [transactions, setTransactions] = useState<P2PTransaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedContact, setSelectedContact] = useState<P2PContact | null>(null);
  const [showSendMoney, setShowSendMoney] = useState(false);
  const [showRequestMoney, setShowRequestMoney] = useState(false);
  const [showAddContact, setShowAddContact] = useState(false);
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [showSplitPayment, setShowSplitPayment] = useState(false);
  const [showQRGenerator, setShowQRGenerator] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [sendMethod, setSendMethod] = useState<'instant' | 'standard'>('instant');
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<string>('');

  useEffect(() => {
      text: `User ${user?.username || 'unknown'} viewed P2P page`,
      page_name: 'P2P',
      user_id: user?.id,
      timestamp: new Date().toISOString()
    });
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      // Fetch accounts
      const accountsData = await accountsService.getAccounts();
      setAccounts(accountsData || []);
      if (accountsData && accountsData.length > 0) {
        setSelectedAccount(accountsData[0].id.toString());
      }

      // Fetch contacts from API
      const contactsData = await p2pApi.getContacts();
      setContacts(contactsData || []);

      // Generate mock transactions for now
    const mockContacts: P2PContact[] = [
      {
        id: '1',
        name: 'Sarah Johnson',
        username: '@sarahj',
        email: 'sarah@example.com',
        phone: '+1 555-0123',
        isFavorite: true,
        lastTransaction: {
          date: '2025-06-14',
          amount: 50,
          type: 'sent',
        },
      },
      {
        id: '2',
        name: 'Mike Chen',
        username: '@mikechen',
        email: 'mike@example.com',
        phone: '+1 555-0124',
        isFavorite: true,
        lastTransaction: {
          date: '2025-06-12',
          amount: 125,
          type: 'received',
        },
      },
      {
        id: '3',
        name: 'Emma Williams',
        username: '@emmaw',
        email: 'emma@example.com',
        phone: '+1 555-0125',
        isFavorite: false,
        lastTransaction: {
          date: '2025-06-10',
          amount: 75,
          type: 'sent',
        },
      },
      {
        id: '4',
        name: 'David Martinez',
        username: '@davidm',
        email: 'david@example.com',
        phone: '+1 555-0126',
        isFavorite: false,
        lastTransaction: {
          date: '2025-06-08',
          amount: 200,
          type: 'received',
        },
      },
      {
        id: '5',
        name: 'Lisa Anderson',
        username: '@lisaa',
        email: 'lisa@example.com',
        phone: '+1 555-0127',
        isFavorite: true,
      },
    ];

    const mockTransactions: P2PTransaction[] = [
      {
        id: '1',
        contact: mockContacts[0],
        amount: 50,
        type: 'sent',
        status: 'completed',
        date: '2025-06-14T15:30:00',
        description: 'Lunch money',
        method: 'instant',
        fee: 0.50,
      },
      {
        id: '2',
        contact: mockContacts[1],
        amount: 125,
        type: 'received',
        status: 'completed',
        date: '2025-06-12T10:15:00',
        description: 'Concert tickets',
        method: 'standard',
      },
      {
        id: '3',
        contact: mockContacts[2],
        amount: 75,
        type: 'sent',
        status: 'pending',
        date: '2025-06-10T18:45:00',
        description: 'Birthday gift',
        method: 'instant',
        fee: 0.75,
      },
      {
        id: '4',
        contact: mockContacts[3],
        amount: 200,
        type: 'received',
        status: 'completed',
        date: '2025-06-08T09:00:00',
        description: 'Rent split',
        method: 'standard',
      },
      {
        id: '5',
        contact: mockContacts[0],
        amount: 30,
        type: 'sent',
        status: 'failed',
        date: '2025-06-05T14:20:00',
        description: 'Coffee',
        method: 'instant',
      },
    ];

      setTransactions(mockTransactions);
      
      // Log data loaded event
        text: `P2P data loaded with ${contactsData?.length || mockContacts.length} contacts and ${mockTransactions.length} transactions`,
        custom_action: 'p2p_data_loaded',
        data: {
          contacts_count: contactsData?.length || mockContacts.length,
          favorites_count: (contactsData || mockContacts).filter(c => c.isFavorite).length,
          transactions_count: mockTransactions.length,
          pending_transactions: mockTransactions.filter(t => t.status === 'pending').length,
          accounts_count: accountsData?.length || 0,
          primary_account: accountsData?.[0]?.name || 'None'
        }
      });
    } catch (error) {
      console.error('Failed to load P2P data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const totalSent = (transactions || [])
    .filter(t => t.type === 'sent' && t.status === 'completed')
    .reduce((sum, t) => sum + t.amount + (t.fee || 0), 0);

  const totalReceived = (transactions || [])
    .filter(t => t.type === 'received' && t.status === 'completed')
    .reduce((sum, t) => sum + t.amount, 0);

  const pendingCount = (transactions || []).filter(t => t.status === 'pending').length;
  const favoriteContacts = (contacts || []).filter(c => c.isFavorite);

  const handleSendMoney = () => {
    if (!selectedContact || !amount || !selectedAccount) return;

    // Find the selected account to check balance
    const account = accounts.find(a => a.id.toString() === selectedAccount);
    if (!account) return;

    // Calculate total amount including fee
    const amountNum = parseFloat(amount);
    const fee = sendMethod === 'instant' ? amountNum * 0.01 : 0;
    const totalAmount = amountNum + fee;

    // Check if account has sufficient balance
    if (account.balance < totalAmount) {
      alert(`Insufficient balance. Your ${account.name} has $${account.balance.toFixed(2)}, but you need $${totalAmount.toFixed(2)} (including ${sendMethod === 'instant' ? '$' + fee.toFixed(2) + ' fee' : 'no fee'}).`);
      return;
    }

      text: `User reviewing P2P payment of $${amount} to ${selectedContact.name} via ${sendMethod} method`,
      custom_action: 'review_p2p_payment',
      data: {
        amount: parseFloat(amount),
        fee: sendMethod === 'instant' ? parseFloat(amount) * 0.01 : 0,
        total_amount: sendMethod === 'instant' ? parseFloat(amount) * 1.01 : parseFloat(amount),
        recipient_name: selectedContact.name,
        recipient_username: selectedContact.username,
        recipient_id: selectedContact.id,
        is_favorite: selectedContact.isFavorite,
        send_method: sendMethod,
        has_description: description.length > 0,
        source_account: accounts.find(a => a.id.toString() === selectedAccount)?.name || 'Unknown',
        source_account_balance: account.balance
      }
    });

    setShowConfirmation(true);
  };

  const handleConfirmSend = async () => {
    if (!selectedContact || !selectedAccount) return;

    try {
      const transferAmount = parseFloat(amount);
      const fee = sendMethod === 'instant' ? transferAmount * 0.01 : 0;
      
      const result = await p2pApi.createTransfer({
        recipient_id: selectedContact.id,
        amount: transferAmount,
        description: description || undefined,
        method: sendMethod,
        source_account_id: selectedAccount
      });

        text: `User successfully sent $${amount} to ${selectedContact.name} via P2P`,
        custom_action: 'p2p_payment_completed',
        data: {
          transaction_id: result?.id,
          amount: transferAmount,
          fee: fee,
          total_amount: transferAmount + fee,
          recipient_name: selectedContact.name,
          recipient_username: selectedContact.username,
          recipient_id: selectedContact.id,
          is_favorite: selectedContact.isFavorite,
          send_method: sendMethod,
          description: description || 'No description',
          source_account: accounts.find(a => a.id.toString() === selectedAccount)?.name || 'Unknown'
        }
      });

      // Refresh data
      loadData();
      
      setShowConfirmation(false);
      setShowSendMoney(false);
      setAmount('');
      setDescription('');
    } catch (error) {
      console.error('Failed to send money:', error);
        error: error instanceof Error ? error.message : 'Unknown error',
        amount: parseFloat(amount),
        recipient: selectedContact.username
      });
    }
  };

  const formatCurrency = (amount: number) => {
    return `$${amount.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  if (isLoading) {
    return (
      <div className="h-[calc(100vh-4rem)]">
        <div className="flex items-center justify-center h-96">
          <div className="text-[var(--text-2)]">Loading P2P payments...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[var(--text-1)]">
              Send & Receive Money
            </h1>
            <p className="text-[var(--text-2)] mt-2">
              Transfer money instantly to friends and family
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-3 mt-4 md:mt-0">
            <Button
              variant="ghost"
              size="sm"
              icon={<Users size={18} />}
              onClick={() => {
                  text: `User opening split payment modal with ${contacts.length} contacts`,
                  custom_action: 'open_split_payment',
                  data: {
                    contacts_count: contacts.length,
                    favorites_count: favoriteContacts.length,
                    accounts_count: accounts.length,
                    from_page: 'p2p'
                  }
                });
                setShowSplitPayment(true);
              }}
            >
              Split
            </Button>
            <Button
              variant="ghost"
              size="sm"
              icon={<DollarSign size={18} />}
              onClick={() => {
                  text: `User opening payment request modal`,
                  custom_action: 'open_payment_request',
                  data: {
                    contacts_count: contacts.length,
                    pending_requests: pendingCount,
                    from_page: 'p2p'
                  }
                });
                setShowRequestMoney(true);
              }}
            >
              Request
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<QrCode size={18} />}
              onClick={() => {
                  text: `User opening QR code generator`,
                  custom_action: 'open_qr_generator',
                  data: {
                    from_page: 'p2p',
                    user_has_transactions: transactions.length > 0
                  }
                });
                setShowQRGenerator(true);
              }}
            >
              QR Code
            </Button>
            <Button
              variant="primary"
              icon={<Send size={18} />}
              onClick={() => {
                  text: `User opening send money modal from P2P header`,
                  custom_action: 'open_send_money',
                  data: {
                    contacts_count: contacts.length,
                    favorites_count: favoriteContacts.length,
                    accounts_count: accounts.length,
                    default_account: accounts[0]?.name || 'None',
                    from_component: 'p2p_header'
                  }
                });
                setShowSendMoney(true);
              }}
            >
              Send Money
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card variant="default" className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-2)]">Total Sent</p>
                <p className="text-2xl font-bold text-[var(--text-1)]">
                  {formatCurrency(totalSent)}
                </p>
              </div>
              <ArrowUpRight className="w-8 h-8 text-[var(--primary-red)] opacity-20" />
            </div>
          </Card>

          <Card variant="default" className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-2)]">Total Received</p>
                <p className="text-2xl font-bold text-[var(--primary-emerald)]">
                  {formatCurrency(totalReceived)}
                </p>
              </div>
              <ArrowDownLeft className="w-8 h-8 text-[var(--primary-emerald)] opacity-20" />
            </div>
          </Card>

          <Card variant="default" className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-2)]">Contacts</p>
                <p className="text-2xl font-bold text-[var(--text-1)]">
                  {contacts.length}
                </p>
              </div>
              <Users className="w-8 h-8 text-[var(--primary-blue)] opacity-20" />
            </div>
          </Card>

          <Card variant="default" className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-2)]">Pending</p>
                <p className="text-2xl font-bold text-[var(--primary-amber)]">
                  {pendingCount}
                </p>
              </div>
              <Clock className="w-8 h-8 text-[var(--primary-amber)] opacity-20" />
            </div>
          </Card>
        </div>

        {/* Quick Send */}
        {favoriteContacts.length > 0 && (
          <P2PQuickSend
            contacts={favoriteContacts}
            onSelectContact={(contact) => {
                text: `User selected favorite contact \"${contact.name}\" from quick send`,
                custom_action: 'select_quick_send_contact',
                data: {
                  contact_id: contact.id,
                  contact_name: contact.name,
                  contact_username: contact.username,
                  last_transaction_type: contact.lastTransaction?.type,
                  last_transaction_amount: contact.lastTransaction?.amount,
                  from_component: 'p2p_quick_send'
                }
              });
              setSelectedContact(contact);
              setShowSendMoney(true);
            }}
          />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Transaction History */}
          <div className="lg:col-span-2">
            <P2PTransactionHistory
              transactions={transactions}
              onSelectTransaction={(transaction) => {
                // Handle transaction selection
                console.log('Selected transaction:', transaction);
              }}
            />
          </div>

          {/* Contacts */}
          <div className="lg:col-span-1">
            <P2PContactList
              contacts={contacts}
              onSelectContact={(contact) => {
                  text: `User selected contact \"${contact.name}\" from contact list`,
                  custom_action: 'select_contact_from_list',
                  data: {
                    contact_id: contact.id,
                    contact_name: contact.name,
                    contact_username: contact.username,
                    is_favorite: contact.isFavorite,
                    has_recent_transaction: !!contact.lastTransaction,
                    from_component: 'p2p_contact_list'
                  }
                });
                setSelectedContact(contact);
                setShowSendMoney(true);
              }}
              onAddContact={() => {
                  text: 'User opening add contact modal from P2P',
                  custom_action: 'open_add_contact',
                  data: {
                    existing_contacts_count: contacts.length,
                    favorites_count: favoriteContacts.length,
                    from_page: 'p2p'
                  }
                });
                setShowAddContact(true);
              }}
            />
          </div>
        </div>
      {/* Send Money Modal */}
      <Modal
        isOpen={showSendMoney}
        onClose={() => {
          setShowSendMoney(false);
          setSelectedContact(null);
          setAmount('');
          setDescription('');
        }}
        title="Send Money"
        size="md"
      >
        {!selectedContact ? (
          <div className="space-y-4">
            <p className="text-[var(--text-2)] mb-4">
              Select a contact to send money to
            </p>
            
            {/* Search Contacts */}
            <Input
              type="text"
              placeholder="Search contacts..."
              value={searchQuery}
              onChange={(e) => {
                const query = e.target.value;
                setSearchQuery(query);
                
                if (query.length > 0) {
                  const filteredCount = contacts.filter(contact => 
                    contact.name.toLowerCase().includes(query.toLowerCase()) ||
                    contact.username.toLowerCase().includes(query.toLowerCase()) ||
                    contact.email.toLowerCase().includes(query.toLowerCase())
                  ).length;
                  
                    text: `User searching P2P contacts with query "${query}"`,
                    search_query: query,
                    data: {
                      total_contacts: contacts.length,
                      matching_contacts: filteredCount,
                      search_context: 'send_money_modal'
                    }
                  });
                }
              }}
              icon={<Search size={18} />}
            />
            
            {/* Contact List */}
            <div className="max-h-96 overflow-y-auto space-y-2">
              {contacts
                .filter(contact => 
                  searchQuery === '' || 
                  contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  contact.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  contact.email.toLowerCase().includes(searchQuery.toLowerCase())
                )
                .map(contact => (
                  <button
                    key={contact.id}
                    onClick={() => {
                        text: `User selected P2P contact "${contact.name}" (@${contact.username}) to send money`,
                        custom_action: 'select_p2p_recipient',
                        data: {
                          contact_id: contact.id,
                          contact_name: contact.name,
                          contact_username: contact.username,
                          is_favorite: contact.isFavorite,
                          has_recent_transaction: !!contact.lastTransaction,
                          last_transaction_type: contact.lastTransaction?.type,
                          last_transaction_amount: contact.lastTransaction?.amount
                        }
                      });
                      setSelectedContact(contact);
                      setSearchQuery('');
                    }}
                    className="w-full p-3 rounded-lg border border-[var(--border-1)] hover:bg-[rgba(var(--glass-rgb),0.1)] transition-all flex items-center gap-3"
                  >
                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[var(--primary-blue)] to-[var(--primary-indigo)] flex items-center justify-center text-white font-medium">
                      {contact.name.charAt(0)}
                    </div>
                    <div className="flex-1 text-left">
                      <p className="font-medium text-[var(--text-1)]">{contact.name}</p>
                      <p className="text-sm text-[var(--text-2)]">{contact.username}</p>
                    </div>
                    {contact.isFavorite && (
                      <Star size={16} className="text-[var(--primary-amber)] fill-current" />
                    )}
                  </button>
                ))
              }
            </div>
            
            {contacts.length === 0 && (
              <div className="text-center py-8">
                <Users className="w-12 h-12 mx-auto mb-3 text-[var(--text-2)] opacity-30" />
                <p className="text-[var(--text-2)]">No contacts found</p>
                <Button
                  variant="primary"
                  size="sm"
                  className="mt-4"
                  onClick={() => {
                    setShowSendMoney(false);
                    setShowAddContact(true);
                  }}
                >
                  Add Contact
                </Button>
              </div>
            )}
          </div>
        ) : !showConfirmation ? (
          <div className="space-y-4">
            {/* Recipient Info */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.05)]">
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
                onClick={() => {
                    text: `User changing recipient from ${selectedContact.name}`,
                    custom_action: 'change_p2p_recipient',
                    data: {
                      previous_contact: selectedContact.name,
                      previous_username: selectedContact.username,
                      had_entered_amount: amount.length > 0,
                      had_entered_description: description.length > 0
                    }
                  });
                  setSelectedContact(null);
                }}
              >
                Change
              </Button>
            </div>

            {/* Amount Input */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                Amount
              </label>
              <Input
                type="number"
                value={amount}
                onChange={(e) => {
                  const newAmount = e.target.value;
                  setAmount(newAmount);
                  
                  if (newAmount && parseFloat(newAmount) > 0) {
                    const amountNum = parseFloat(newAmount);
                    const fee = sendMethod === 'instant' ? amountNum * 0.01 : 0;
                    
                      text: `User entered P2P amount $${newAmount} to ${selectedContact.name}${fee > 0 ? ` (fee: $${fee.toFixed(2)})` : ''}`,
                      field_name: 'p2p_amount',
                      field_value: newAmount,
                      data: {
                        amount: amountNum,
                        fee: fee,
                        total_amount: amountNum + fee,
                        recipient: selectedContact.username,
                        send_method: sendMethod,
                        selected_account: selectedAccount
                      }
                    });
                  }
                }}
                placeholder="0.00"
                icon={<DollarSign size={18} />}
                size="lg"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                Description (optional)
              </label>
              <Input
                type="text"
                value={description}
                onChange={(e) => {
                  const desc = e.target.value;
                  setDescription(desc);
                  
                  if (desc.length > 0) {
                      text: `User entered P2P description: "${desc.substring(0, 50)}${desc.length > 50 ? '...' : ''}"`,
                      field_name: 'p2p_description',
                      field_value: desc,
                      data: {
                        description_length: desc.length,
                        recipient: selectedContact.username,
                        amount: amount ? parseFloat(amount) : 0
                      }
                    });
                  }
                }}
                placeholder="What's this for?"
                icon={<MessageSquare size={18} />}
              />
            </div>

            {/* Account Selection */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                From Account
              </label>
              <Dropdown
                value={selectedAccount}
                onChange={(value) => {
                  const previousAccount = accounts.find(a => a.id.toString() === selectedAccount);
                  const newAccount = accounts.find(a => a.id.toString() === value);
                  setSelectedAccount(value);
                  
                  if (newAccount) {
                      text: `User selected P2P source account "${newAccount.name}" with balance $${newAccount.balance.toFixed(2)}`,
                      custom_action: 'select_p2p_source_account',
                      data: {
                        account_id: value,
                        account_name: newAccount.name,
                        account_balance: newAccount.balance,
                        previous_account: previousAccount?.name,
                        amount_to_send: amount ? parseFloat(amount) : 0,
                        has_sufficient_balance: amount ? newAccount.balance >= parseFloat(amount) * (sendMethod === 'instant' ? 1.01 : 1) : true
                      }
                    });
                  }
                }}
                items={accounts.map(account => ({
                  value: account.id.toString(),
                  label: `${account.name} - $${account.balance.toFixed(2)}`
                }))}
                placeholder="Select an account"
                fullWidth
              />
            </div>

            {/* Send Method */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
                Send Method
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => {
                    if (sendMethod !== 'instant') {
                      setSendMethod('instant');
                      
                      const amountNum = amount ? parseFloat(amount) : 0;
                      const newFee = amountNum * 0.01;
                      
                        text: `User switched to instant P2P transfer (1% fee: $${newFee.toFixed(2)})`,
                        custom_action: 'change_p2p_send_method',
                        data: {
                          from_method: sendMethod,
                          to_method: 'instant',
                          amount: amountNum,
                          old_fee: 0,
                          new_fee: newFee,
                          total_with_new_fee: amountNum + newFee,
                          recipient: selectedContact.username
                        }
                      });
                    }
                  }}
                  className={`
                    p-3 rounded-lg border transition-all
                    ${sendMethod === 'instant'
                      ? 'border-[var(--primary-blue)] bg-[rgba(var(--primary-blue),0.1)]'
                      : 'border-[var(--border-1)] hover:bg-[rgba(var(--glass-rgb),0.1)]'
                    }
                  `}
                >
                  <Zap className="w-5 h-5 mx-auto mb-1 text-[var(--primary-blue)]" />
                  <p className="text-sm font-medium text-[var(--text-1)]">Instant</p>
                  <p className="text-xs text-[var(--text-2)] mt-1">Fee: 1%</p>
                </button>
                
                <button
                  onClick={() => {
                    if (sendMethod !== 'standard') {
                      setSendMethod('standard');
                      
                      const amountNum = amount ? parseFloat(amount) : 0;
                      const oldFee = amountNum * 0.01;
                      
                        text: `User switched to standard P2P transfer (free, 1-3 days)`,
                        custom_action: 'change_p2p_send_method',
                        data: {
                          from_method: sendMethod,
                          to_method: 'standard',
                          amount: amountNum,
                          old_fee: oldFee,
                          new_fee: 0,
                          total_with_new_fee: amountNum,
                          recipient: selectedContact.username
                        }
                      });
                    }
                  }}
                  className={`
                    p-3 rounded-lg border transition-all
                    ${sendMethod === 'standard'
                      ? 'border-[var(--primary-blue)] bg-[rgba(var(--primary-blue),0.1)]'
                      : 'border-[var(--border-1)] hover:bg-[rgba(var(--glass-rgb),0.1)]'
                    }
                  `}
                >
                  <Clock className="w-5 h-5 mx-auto mb-1 text-[var(--primary-amber)]" />
                  <p className="text-sm font-medium text-[var(--text-1)]">Standard</p>
                  <p className="text-xs text-[var(--text-2)] mt-1">Free • 1-3 days</p>
                </button>
              </div>
            </div>

            {/* Fee Info and Balance Check */}
            {amount && (
              <div className="space-y-3">
                {sendMethod === 'instant' && (
                  <div className="p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-[var(--text-2)]">Amount</span>
                      <span className="text-[var(--text-1)]">{formatCurrency(parseFloat(amount))}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[var(--text-2)]">Fee (1%)</span>
                      <span className="text-[var(--text-1)]">{formatCurrency(parseFloat(amount) * 0.01)}</span>
                    </div>
                    <div className="flex justify-between text-sm font-medium pt-2 border-t border-[var(--border-1)]">
                      <span className="text-[var(--text-1)]">Total</span>
                      <span className="text-[var(--text-1)]">{formatCurrency(parseFloat(amount) * 1.01)}</span>
                    </div>
                  </div>
                )}
                
                {/* Balance Warning */}
                {(() => {
                  const account = accounts.find(a => a.id.toString() === selectedAccount);
                  if (!account) return null;
                  
                  const amountNum = parseFloat(amount);
                  const fee = sendMethod === 'instant' ? amountNum * 0.01 : 0;
                  const totalAmount = amountNum + fee;
                  
                  if (account.balance < totalAmount) {
                    return (
                      <div className="p-3 rounded-lg bg-[rgba(var(--primary-red),0.1)] border border-[var(--primary-red)]">
                        <p className="text-sm text-[var(--primary-red)] font-medium">
                          Insufficient balance
                        </p>
                        <p className="text-xs text-[var(--text-2)] mt-1">
                          Available: {formatCurrency(account.balance)} • Required: {formatCurrency(totalAmount)}
                        </p>
                      </div>
                    );
                  }
                  return null;
                })()}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                variant="secondary"
                fullWidth
                onClick={() => {
                  setShowSendMoney(false);
                  setSelectedContact(null);
                  setAmount('');
                  setDescription('');
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                fullWidth
                onClick={handleSendMoney}
                disabled={!amount || parseFloat(amount) <= 0 || (() => {
                  const account = accounts.find(a => a.id.toString() === selectedAccount);
                  if (!account) return true;
                  const amountNum = parseFloat(amount);
                  const fee = sendMethod === 'instant' ? amountNum * 0.01 : 0;
                  return account.balance < (amountNum + fee);
                })()}
              >
                Review & Send
              </Button>
            </div>
          </div>
        ) : showConfirmation && selectedContact ? (
          <div className="space-y-4">
            <div className="text-center py-4">
              <CheckCircle className="w-12 h-12 mx-auto mb-3 text-[var(--primary-emerald)]" />
              <h3 className="text-xl font-semibold text-[var(--text-1)] mb-2">
                Confirm Payment
              </h3>
              <p className="text-3xl font-bold text-[var(--text-1)]">
                {formatCurrency(parseFloat(amount))}
              </p>
              <p className="text-sm text-[var(--text-2)] mt-2">
                to {selectedContact.name}
              </p>
            </div>

            <SlideToConfirm
              amount={parseFloat(amount)}
              recipient={selectedContact.name}
              onConfirm={handleConfirmSend}
            />
          </div>
        ) : null}
      </Modal>

      {/* Add Contact Modal */}
      <Modal
        isOpen={showAddContact}
        onClose={() => setShowAddContact(false)}
        title="Add Contact"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-[var(--text-2)]">
            Contact addition form will be implemented here.
          </p>
        </div>
      </Modal>

      {/* Split Payment Modal */}
      <SplitPaymentModal
        isOpen={showSplitPayment}
        onClose={() => setShowSplitPayment(false)}
        accounts={accounts}
        contacts={contacts}
        onSuccess={loadData}
      />

      {/* Payment Request Modal */}
      <PaymentRequestModal
        isOpen={showRequestMoney}
        onClose={() => setShowRequestMoney(false)}
        contacts={contacts}
        onSuccess={loadData}
      />

      {/* QR Code Modal - Generate */}
      <QRCodeModal
        isOpen={showQRGenerator}
        onClose={() => setShowQRGenerator(false)}
        mode="generate"
      />

      {/* QR Code Modal - Scan */}
      <QRCodeModal
        isOpen={showQRScanner}
        onClose={() => setShowQRScanner(false)}
        mode="scan"
        onScanSuccess={(data) => {
          console.log('Scanned data:', data);
          setShowQRScanner(false);
        }}
      />
    </div>
  );
}
