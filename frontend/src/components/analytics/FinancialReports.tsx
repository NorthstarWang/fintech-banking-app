"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Download,
  TrendingUp,
  DollarSign,
  PieChart,
  BarChart3,
  Target,
  AlertCircle
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { analyticsService, BudgetPerformance, GoalProgress } from '@/lib/api/analytics';

interface FinancialReportsProps {
  onGenerateReport: (type: string) => void;
}

export default function FinancialReports({ onGenerateReport }: FinancialReportsProps) {
  const [budgetPerformance, setBudgetPerformance] = useState<{
    budget_count: number;
    over_budget_count: number;
    at_risk_count: number;
    performance: BudgetPerformance[];
  } | null>(null);
  
  const [goalsProgress, setGoalsProgress] = useState<{
    active_goals: number;
    completed_goals: number;
    total_target_amount: number;
    total_saved_amount: number;
    overall_progress: number;
    goal_projections: GoalProgress[];
  } | null>(null);
  
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [budget, goals] = await Promise.all([
        analyticsService.getBudgetPerformance(),
        analyticsService.getGoalsProgress()
      ]);
      
      setBudgetPerformance(budget);
      setGoalsProgress(goals);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const reportTypes = [
    {
      id: 'monthly-summary',
      title: 'Monthly Financial Summary',
      description: 'Comprehensive overview of income, expenses, and savings',
      icon: <FileText className="w-5 h-5" />,
      color: 'var(--primary-blue)'
    },
    {
      id: 'budget-analysis',
      title: 'Budget Performance Report',
      description: 'Detailed analysis of budget adherence and spending patterns',
      icon: <PieChart className="w-5 h-5" />,
      color: 'var(--primary-amber)'
    },
    {
      id: 'investment-summary',
      title: 'Investment & Growth Report',
      description: 'Track portfolio performance and net worth growth',
      icon: <TrendingUp className="w-5 h-5" />,
      color: 'var(--primary-emerald)'
    },
    {
      id: 'tax-preparation',
      title: 'Tax Preparation Report',
      description: 'Categorized expenses and income for tax filing',
      icon: <BarChart3 className="w-5 h-5" />,
      color: 'var(--primary-purple)'
    }
  ];

  if (loading) {
    return (
      <Card variant="default">
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
            <div className="space-y-3">
              <div className="h-20 bg-gray-200 rounded" />
              <div className="h-20 bg-gray-200 rounded" />
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card variant="subtle">
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-[var(--text-2)]">Active Budgets</p>
              <DollarSign className="w-4 h-4 text-[var(--primary-blue)]" />
            </div>
            <p className="text-2xl font-bold text-[var(--text-1)]">
              {budgetPerformance?.budget_count || 0}
            </p>
            <p className="text-xs text-[var(--text-2)] mt-1">
              {budgetPerformance?.over_budget_count || 0} over budget
            </p>
          </div>
        </Card>

        <Card variant="subtle">
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-[var(--text-2)]">At Risk Budgets</p>
              <AlertCircle className="w-4 h-4 text-[var(--primary-amber)]" />
            </div>
            <p className="text-2xl font-bold text-[var(--text-1)]">
              {budgetPerformance?.at_risk_count || 0}
            </p>
            <p className="text-xs text-[var(--text-2)] mt-1">
              80-100% utilized
            </p>
          </div>
        </Card>

        <Card variant="subtle">
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-[var(--text-2)]">Active Goals</p>
              <Target className="w-4 h-4 text-[var(--primary-emerald)]" />
            </div>
            <p className="text-2xl font-bold text-[var(--text-1)]">
              {goalsProgress?.active_goals || 0}
            </p>
            <p className="text-xs text-[var(--text-2)] mt-1">
              {goalsProgress?.completed_goals || 0} completed
            </p>
          </div>
        </Card>

        <Card variant="subtle">
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-[var(--text-2)]">Goals Progress</p>
              <TrendingUp className="w-4 h-4 text-[var(--primary-purple)]" />
            </div>
            <p className="text-2xl font-bold text-[var(--text-1)]">
              {goalsProgress?.overall_progress.toFixed(0) || 0}%
            </p>
            <p className="text-xs text-[var(--text-2)] mt-1">
              ${goalsProgress?.total_saved_amount.toLocaleString() || 0} saved
            </p>
          </div>
        </Card>
      </div>

      {/* Available Reports */}
      <Card variant="default">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-[var(--text-1)] mb-6">
            Generate Financial Reports
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reportTypes.map((report, index) => (
              <motion.div
                key={report.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card variant="subtle" className="hover:shadow-lg transition-shadow">
                  <div className="p-5">
                    <div className="flex items-start gap-4">
                      <div
                        className="p-3 rounded-lg"
                        style={{ backgroundColor: `${report.color}20` }}
                      >
                        <div style={{ color: report.color }}>
                          {report.icon}
                        </div>
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-[var(--text-1)] mb-1">
                          {report.title}
                        </h4>
                        <p className="text-sm text-[var(--text-2)] mb-3">
                          {report.description}
                        </p>
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={<Download size={16} />}
                          onClick={() => onGenerateReport(report.id)}
                        >
                          Generate Report
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </Card>

      {/* Budget Performance Details */}
      {budgetPerformance && budgetPerformance.performance.length > 0 && (
        <Card variant="default">
          <div className="p-6">
            <h4 className="text-md font-semibold text-[var(--text-1)] mb-4">
              Budget Performance Overview
            </h4>
            
            <div className="space-y-3">
              {budgetPerformance.performance.slice(0, 5).map((budget) => (
                <div
                  key={budget.budget_id}
                  className="flex items-center justify-between p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.05)]"
                >
                  <div>
                    <p className="font-medium text-[var(--text-1)]">
                      {budget.category_name}
                    </p>
                    <p className="text-xs text-[var(--text-2)]">
                      {budget.period} budget
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-[var(--text-1)]">
                      ${budget.spent_amount.toFixed(2)} / ${budget.budgeted_amount.toFixed(2)}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all ${
                            budget.percentage_used > 100
                              ? 'bg-[var(--primary-red)]'
                              : budget.percentage_used > 80
                              ? 'bg-[var(--primary-amber)]'
                              : 'bg-[var(--primary-emerald)]'
                          }`}
                          style={{ width: `${Math.min(budget.percentage_used, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-[var(--text-2)]">
                        {budget.percentage_used.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Goals Progress Details */}
      {goalsProgress && goalsProgress.goal_projections.length > 0 && (
        <Card variant="default">
          <div className="p-6">
            <h4 className="text-md font-semibold text-[var(--text-1)] mb-4">
              Goals Progress Tracking
            </h4>
            
            <div className="space-y-3">
              {goalsProgress.goal_projections.slice(0, 5).map((goal) => (
                <div
                  key={goal.goal_id}
                  className="flex items-center justify-between p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.05)]"
                >
                  <div>
                    <p className="font-medium text-[var(--text-1)]">
                      {goal.goal_name}
                    </p>
                    <p className="text-xs text-[var(--text-2)]">
                      Target: {goal.target_date ? new Date(goal.target_date).toLocaleDateString() : 'No target date'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-[var(--text-1)]">
                      ${goal.current_amount.toFixed(2)} / ${goal.target_amount.toFixed(2)}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[var(--primary-blue)] transition-all"
                          style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-[var(--text-2)]">
                        {goal.progress_percentage.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}