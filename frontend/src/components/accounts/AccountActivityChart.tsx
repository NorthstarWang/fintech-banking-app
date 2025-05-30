import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, DollarSign, Calendar } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';

interface AccountActivityChartProps {
  account: {
    id: string;
    name: string;
    type: string;
    balance: number;
  };
  showBalances: boolean;
}

export const AccountActivityChart: React.FC<AccountActivityChartProps> = ({ 
  account, 
  showBalances 
}) => {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('month');

  // Mock data for the chart
  const generateMockData = () => {
    const days = timeRange === 'week' ? 7 : timeRange === 'month' ? 30 : 365;
    const data = [];
    const baseBalance = Math.abs(account.balance) || 5000; // Use absolute value to handle negative balances
    let balance = baseBalance * 0.8; // Start from 80% of current balance

    for (let i = 0; i < days; i++) {
      // Generate more realistic changes based on account type
      const maxChange = account.type === 'credit' ? 200 : 500;
      const change = (Math.random() - 0.5) * maxChange;
      balance = Math.max(100, balance + change); // Keep minimum balance of $100
      
      data.push({
        day: i,
        balance: balance,
        change: change,
      });
    }
    
    // Ensure the last data point is close to current balance
    if (data.length > 0) {
      data[data.length - 1].balance = Math.abs(account.balance) || baseBalance;
    }
    
    return data;
  };

  const chartData = generateMockData();
  const maxBalance = Math.max(...chartData.map(d => d.balance));
  const minBalance = Math.min(...chartData.map(d => d.balance));
  const balanceRange = Math.max(1, maxBalance - minBalance); // Prevent division by zero

  const averageBalance = chartData.reduce((sum, d) => sum + d.balance, 0) / chartData.length;
  const totalInflow = chartData.filter(d => d.change > 0).reduce((sum, d) => sum + d.change, 0);
  const totalOutflow = Math.abs(chartData.filter(d => d.change < 0).reduce((sum, d) => sum + d.change, 0));

  const formatCurrency = (amount: number) => {
    return `$${Math.abs(amount).toLocaleString('en-US', { 
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })}`;
  };

  return (
    <Card variant="default" data-testid="account-activity-chart">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-[var(--text-1)]">
            Account Activity
          </h3>
          <div className="flex gap-2">
            <Button
              variant={timeRange === 'week' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setTimeRange('week')}
              data-testid="time-range-week"
            >
              Week
            </Button>
            <Button
              variant={timeRange === 'month' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setTimeRange('month')}
              data-testid="time-range-month"
            >
              Month
            </Button>
            <Button
              variant={timeRange === 'year' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setTimeRange('year')}
              data-testid="time-range-year"
            >
              Year
            </Button>
          </div>
        </div>

        {/* Chart Container */}
        <div className="relative h-64 mb-6 overflow-hidden">
          <div className="absolute inset-0 flex items-end">
            <div className="w-full h-full relative">
              {/* Y-axis labels */}
              <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-[var(--text-2)]">
                <span>{showBalances ? formatCurrency(maxBalance) : '•••'}</span>
                <span>{showBalances ? formatCurrency((maxBalance + minBalance) / 2) : '•••'}</span>
                <span>{showBalances ? formatCurrency(minBalance) : '•••'}</span>
              </div>

              {/* Chart bars */}
              <div className="ml-12 h-full flex items-end gap-1 pr-4">
                {chartData.slice(0, timeRange === 'year' ? 52 : chartData.length).map((data, index) => {
                  const height = Math.max(2, ((data.balance - minBalance) / balanceRange) * 100);
                  const isPositive = data.change > 0;
                  
                  // Hover tracking handled inline

                  return (
                    <div
                      key={index}
                      className="flex-1 relative h-full flex items-end min-w-[2px] group"
                      data-testid={`chart-bar-container-${index}`}
                    >
                      <motion.div
                        className={`
                          w-full rounded-t
                          ${isPositive 
                            ? 'bg-gradient-to-t from-[var(--primary-emerald)] to-[var(--primary-teal)]' 
                            : 'bg-gradient-to-t from-[var(--primary-blue)] to-[var(--primary-indigo)]'
                          }
                          opacity-80 hover:opacity-100 transition-opacity cursor-pointer
                        `}
                        style={{ height: `${height}%` }}
                        initial={{ scaleY: 0 }}
                        animate={{ scaleY: 1 }}
                        transition={{ delay: index * 0.01, duration: 0.5, ease: 'easeOut' }}
                        onMouseEnter={() => {
                            text: `User hovered over Activity Chart Bar ${index + 1} - ${showBalances ? formatCurrency(data.balance) : 'Hidden'}`,
                            element_identifier: `activity-chart-bar-${index}`,
                            data: {
                              bar_index: index,
                              balance: showBalances ? data.balance : null,
                              change: showBalances ? data.change : null
                            }
                          });
                        }}
                      >
                      
                      {/* Tooltip */}
                      <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                        <div className="bg-[var(--bg-color)] border border-[var(--border-1)] rounded-lg shadow-lg p-2 whitespace-nowrap">
                          <p className="text-xs font-medium text-[var(--text-1)]">
                            {showBalances ? formatCurrency(data.balance) : '••••••'}
                          </p>
                          <p className={`text-xs ${isPositive ? 'text-[var(--primary-emerald)]' : 'text-[var(--primary-red)]'}`}>
                            {isPositive ? '+' : ''}{showBalances ? formatCurrency(data.change) : '•••'}
                          </p>
                        </div>
                      </div>
                      </motion.div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Trend line */}
          <div className="absolute inset-0 ml-12 pr-4 pointer-events-none">
            <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
              <motion.path
                d={chartData.slice(0, timeRange === 'year' ? 52 : chartData.length).map((data, index, arr) => {
                  const x = (index / Math.max(1, arr.length - 1)) * 100;
                  const y = Math.max(0, Math.min(100, 100 - ((data.balance - minBalance) / balanceRange) * 100));
                  return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
                }).join(' ')}
                fill="none"
                stroke="var(--primary-violet)"
                strokeWidth="2"
                strokeDasharray="5,5"
                opacity="0.5"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1.5, ease: 'easeInOut' }}
              />
            </svg>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4">
          <div 
            className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] border border-[var(--border-1)] cursor-pointer transition-all hover:bg-[rgba(var(--glass-rgb),0.15)]"
            data-testid="stat-average-balance"
            onMouseEnter={() => {
                text: `User hovered over Average Balance Stat - ${showBalances ? formatCurrency(averageBalance) : 'Hidden'}`,
                element_identifier: 'stat-average-balance',
                data: {
                  average_balance: showBalances ? averageBalance : null
                }
              });
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-4 h-4 text-[var(--text-2)]" />
              <p className="text-sm text-[var(--text-2)]">Average Balance</p>
            </div>
            <p className="text-lg font-semibold text-[var(--text-1)]">
              {showBalances ? formatCurrency(averageBalance) : '••••••'}
            </p>
          </div>

          <div 
            className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] border border-[var(--border-1)] cursor-pointer transition-all hover:bg-[rgba(var(--glass-rgb),0.15)]"
            data-testid="stat-total-inflow"
            onMouseEnter={() => {
                text: `User hovered over Total Inflow Stat - ${showBalances ? formatCurrency(totalInflow) : 'Hidden'}`,
                element_identifier: 'stat-total-inflow',
                data: {
                  total_inflow: showBalances ? totalInflow : null
                }
              });
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-[var(--primary-emerald)]" />
              <p className="text-sm text-[var(--text-2)]">Total Inflow</p>
            </div>
            <p className="text-lg font-semibold text-[var(--primary-emerald)]">
              {showBalances ? `+${formatCurrency(totalInflow)}` : '••••••'}
            </p>
          </div>

          <div 
            className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] border border-[var(--border-1)] cursor-pointer transition-all hover:bg-[rgba(var(--glass-rgb),0.15)]"
            data-testid="stat-total-outflow"
            onMouseEnter={() => {
                text: `User hovered over Total Outflow Stat - ${showBalances ? formatCurrency(totalOutflow) : 'Hidden'}`,
                element_identifier: 'stat-total-outflow',
                data: {
                  total_outflow: showBalances ? totalOutflow : null
                }
              });
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="w-4 h-4 text-[var(--primary-red)]" />
              <p className="text-sm text-[var(--text-2)]">Total Outflow</p>
            </div>
            <p className="text-lg font-semibold text-[var(--primary-red)]">
              {showBalances ? `-${formatCurrency(totalOutflow)}` : '••••••'}
            </p>
          </div>
        </div>

        {/* Insights */}
        <div className="mt-6 p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] border border-[var(--border-1)]">
          <h4 className="font-medium text-[var(--text-1)] mb-2 flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Insights
          </h4>
          <ul className="space-y-2 text-sm text-[var(--text-2)]">
            <li className="flex items-start gap-2">
              <span className="text-[var(--primary-blue)]">•</span>
              <span>
                Your balance has {account.balance > averageBalance ? 'increased' : 'decreased'} by{' '}
                {showBalances 
                  ? formatCurrency(Math.abs(account.balance - averageBalance))
                  : '••••••'
                } compared to your {timeRange}ly average
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--primary-emerald)]">•</span>
              <span>
                Highest balance this {timeRange}:{' '}
                {showBalances ? formatCurrency(maxBalance) : '••••••'}
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--primary-indigo)]">•</span>
              <span>
                Net cash flow:{' '}
                <span className={totalInflow - totalOutflow > 0 ? 'text-[var(--primary-emerald)]' : 'text-[var(--primary-red)]'}>
                  {showBalances 
                    ? `${totalInflow - totalOutflow > 0 ? '+' : ''}${formatCurrency(totalInflow - totalOutflow)}`
                    : '••••••'
                  }
                </span>
              </span>
            </li>
          </ul>
        </div>
      </div>
    </Card>
  );
};

export default AccountActivityChart;
