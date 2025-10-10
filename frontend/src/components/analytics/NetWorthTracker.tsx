"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PiggyBank,
  CreditCard,
  Home
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Dropdown from '@/components/ui/Dropdown';
import { analyticsService, NetWorthHistory } from '@/lib/api/analytics';
import { accountsService, Account } from '@/lib/api';

interface NetWorthTrackerProps {
  onExport?: () => void;
}

export default function NetWorthTracker({ onExport }: NetWorthTrackerProps) {
  const [netWorthHistory, setNetWorthHistory] = useState<NetWorthHistory[]>([]);
  const [currentNetWorth, setCurrentNetWorth] = useState(0);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [monthsBack, setMonthsBack] = useState(12);

  useEffect(() => {
    loadData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monthsBack]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [netWorthData, accountsData] = await Promise.all([
        analyticsService.getNetWorthHistory(monthsBack),
        accountsService.getAccounts()
      ]);
      
      setNetWorthHistory(netWorthData.history);
      setCurrentNetWorth(netWorthData.current_net_worth);
      setAccounts(accountsData);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const calculateAssets = () => {
    return accounts
      .filter(acc => ['checking', 'savings', 'investment'].includes(acc.account_type))
      .reduce((sum, acc) => sum + acc.balance, 0);
  };

  const calculateLiabilities = () => {
    return accounts
      .filter(acc => ['credit_card', 'loan'].includes(acc.account_type))
      .reduce((sum, acc) => sum + Math.abs(acc.balance), 0);
  };

  const getNetWorthChange = () => {
    if (netWorthHistory.length < 2) return { amount: 0, percentage: 0 };
    
    const current = netWorthHistory[netWorthHistory.length - 1].net_worth;
    const previous = netWorthHistory[netWorthHistory.length - 2].net_worth;
    const change = current - previous;
    const percentage = previous !== 0 ? (change / Math.abs(previous)) * 100 : 0;
    
    return { amount: change, percentage };
  };

  const getAccountIcon = (type: string) => {
    switch (type) {
      case 'checking':
      case 'savings':
        return <PiggyBank className="w-4 h-4" />;
      case 'investment':
        return <TrendingUp className="w-4 h-4" />;
      case 'credit_card':
        return <CreditCard className="w-4 h-4" />;
      case 'loan':
        return <Home className="w-4 h-4" />;
      default:
        return <DollarSign className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <Card variant="default">
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
            <div className="h-64 bg-gray-200 rounded" />
          </div>
        </div>
      </Card>
    );
  }

  const netWorthChange = getNetWorthChange();
  const totalAssets = calculateAssets();
  const totalLiabilities = calculateLiabilities();

  // Find min and max for chart scaling
  const minNetWorth = Math.min(...netWorthHistory.map(h => h.net_worth));
  const maxNetWorth = Math.max(...netWorthHistory.map(h => h.net_worth));
  const range = maxNetWorth - minNetWorth || 1;

  return (
    <div className="space-y-6">
      {/* Current Net Worth */}
      <Card variant="default">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-[var(--text-1)]">Net Worth Tracking</h3>
            <div className="flex items-center gap-2">
              <Dropdown
                value={monthsBack.toString()}
                onChange={(value) => setMonthsBack(Number(value))}
                items={[
                  { value: '6', label: '6 months' },
                  { value: '12', label: '12 months' },
                  { value: '24', label: '24 months' },
                  { value: '36', label: '36 months' },
                ]}
              />
              {onExport && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={onExport}
                >
                  Export
                </Button>
              )}
            </div>
          </div>

          {/* Current Net Worth Display */}
          <div className="mb-8">
            <p className="text-sm text-[var(--text-2)] mb-2">Current Net Worth</p>
            <div className="flex items-end gap-4">
              <h2 className="text-3xl font-bold text-[var(--text-1)]">
                ${currentNetWorth.toLocaleString('en-US', { 
                  minimumFractionDigits: 2, 
                  maximumFractionDigits: 2 
                })}
              </h2>
              <div className={`flex items-center gap-1 ${
                netWorthChange.amount >= 0 
                  ? 'text-[var(--primary-emerald)]' 
                  : 'text-[var(--primary-red)]'
              }`}>
                {netWorthChange.amount >= 0 ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                <span className="text-sm font-medium">
                  {netWorthChange.amount >= 0 ? '+' : ''}
                  ${Math.abs(netWorthChange.amount).toLocaleString('en-US', { 
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: 2 
                  })}
                  ({netWorthChange.percentage >= 0 ? '+' : ''}{netWorthChange.percentage.toFixed(1)}%)
                </span>
              </div>
            </div>
          </div>

          {/* Net Worth Chart */}
          <div className="mb-6">
            <div className="h-48 relative">
              <svg className="w-full h-full" viewBox={`0 0 ${netWorthHistory.length * 50} 200`}>
                {/* Grid lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((y) => (
                  <line
                    key={y}
                    x1="0"
                    y1={y * 180 + 10}
                    x2={netWorthHistory.length * 50}
                    y2={y * 180 + 10}
                    stroke="rgba(var(--glass-rgb), 0.2)"
                    strokeDasharray="5,5"
                  />
                ))}
                
                {/* Line chart */}
                <polyline
                  fill="none"
                  stroke="var(--primary-blue)"
                  strokeWidth="2"
                  points={netWorthHistory.map((history, index) => {
                    const x = index * 50 + 25;
                    const y = 190 - ((history.net_worth - minNetWorth) / range) * 180;
                    return `${x},${y}`;
                  }).join(' ')}
                />
                
                {/* Data points */}
                {netWorthHistory.map((history, index) => {
                  const x = index * 50 + 25;
                  const y = 190 - ((history.net_worth - minNetWorth) / range) * 180;
                  
                  return (
                    <g key={index}>
                      <circle
                        cx={x}
                        cy={y}
                        r="4"
                        fill="var(--primary-blue)"
                        className="cursor-pointer hover:r-6"
                      />
                      <title>
                        {new Date(history.date).toLocaleDateString()}: ${history.net_worth.toLocaleString()}
                      </title>
                    </g>
                  );
                })}
              </svg>
            </div>
            
            {/* X-axis labels */}
            <div className="flex justify-between text-xs text-[var(--text-2)] mt-2">
              {netWorthHistory.filter((_, i) => i % Math.ceil(netWorthHistory.length / 6) === 0).map((history) => (
                <span key={history.date}>
                  {new Date(history.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}
                </span>
              ))}
            </div>
          </div>

          {/* Assets vs Liabilities */}
          <div className="grid grid-cols-2 gap-4">
            <Card variant="subtle">
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-[var(--text-2)]">Total Assets</p>
                  <TrendingUp className="w-4 h-4 text-[var(--primary-emerald)]" />
                </div>
                <p className="text-xl font-semibold text-[var(--text-1)]">
                  ${totalAssets.toLocaleString('en-US', { 
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: 2 
                  })}
                </p>
              </div>
            </Card>
            
            <Card variant="subtle">
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-[var(--text-2)]">Total Liabilities</p>
                  <TrendingDown className="w-4 h-4 text-[var(--primary-red)]" />
                </div>
                <p className="text-xl font-semibold text-[var(--text-1)]">
                  ${totalLiabilities.toLocaleString('en-US', { 
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: 2 
                  })}
                </p>
              </div>
            </Card>
          </div>
        </div>
      </Card>

      {/* Account Breakdown */}
      <Card variant="default">
        <div className="p-6">
          <h4 className="text-md font-semibold text-[var(--text-1)] mb-4">Account Breakdown</h4>
          
          <div className="space-y-3">
            {accounts.map((account) => {
              const isAsset = ['checking', 'savings', 'investment'].includes(account.account_type);
              const balance = isAsset ? account.balance : -Math.abs(account.balance);
              
              return (
                <motion.div
                  key={account.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center justify-between p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.05)]"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${
                      isAsset 
                        ? 'bg-[rgba(var(--primary-emerald),0.1)]' 
                        : 'bg-[rgba(var(--primary-red),0.1)]'
                    }`}>
                      {getAccountIcon(account.account_type)}
                    </div>
                    <div>
                      <p className="font-medium text-[var(--text-1)]">{account.name}</p>
                      <p className="text-xs text-[var(--text-2)]">
                        {account.account_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </p>
                    </div>
                  </div>
                  <p className={`font-semibold ${
                    balance >= 0 
                      ? 'text-[var(--primary-emerald)]' 
                      : 'text-[var(--primary-red)]'
                  }`}>
                    {balance >= 0 ? '+' : '-'}${Math.abs(balance).toLocaleString('en-US', { 
                      minimumFractionDigits: 2, 
                      maximumFractionDigits: 2 
                    })}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </Card>
    </div>
  );
}