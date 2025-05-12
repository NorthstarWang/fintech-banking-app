'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Target,
  Plus,
  Trophy,
  TrendingUp,
  Calendar,
  DollarSign,
  Filter,
  CheckCircle,
  Clock,
  AlertCircle,
  Zap,
  Home,
  Car,
  GraduationCap,
  Plane,
  Heart,
  Gift,
  PiggyBank,
  Briefcase
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import Dropdown from '@/components/ui/Dropdown';
import DatePicker from '@/components/ui/DatePicker';
import GoalCard from '@/components/goals/GoalCard';
import GoalProgress from '@/components/goals/GoalProgress';
import GoalMilestones from '@/components/goals/GoalMilestones';
import { goalsService, GoalCreate, GoalUpdate } from '@/lib/api/goals';
import { useAuth } from '@/contexts/AuthContext';
import { useAlert } from '@/contexts/AlertContext';

export interface Goal {
  id: string;
  name: string;
  description?: string;
  category: 'SAVINGS' | 'DEBT' | 'INVESTMENT' | 'PURCHASE' | 'OTHER';
  icon?: React.ReactNode;
  targetAmount: number;
  currentAmount: number;
  deadline: string;
  createdAt: string;
  status: 'active' | 'completed' | 'paused';
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  progress: number;
  monthlyContribution: number;
  automatedSaving: boolean;
  milestones: {
    amount: number;
    description: string;
    reached: boolean;
    reachedDate?: string;
  }[];
  projectedCompletion?: string;
  riskLevel: 'on-track' | 'at-risk' | 'off-track';
}

export default function GoalsPage() {
  const { user } = useAuth();
  const { showError, showSuccess, showInfo } = useAlert();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'deadline' | 'progress' | 'amount'>('deadline');
  const [showCreateGoal, setShowCreateGoal] = useState(false);
  const [showGoalDetails, setShowGoalDetails] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditMode, setIsEditMode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [goalForm, setGoalForm] = useState<{
    name: string;
    description: string;
    targetAmount: string;
    initialAmount: string;
    targetDate: string;
    category: GoalCreate['category'];
    priority: GoalCreate['priority'];
  }>({
    name: '',
    description: '',
    targetAmount: '',
    initialAmount: '0',
    targetDate: '',
    category: 'SAVINGS',
    priority: 'MEDIUM'
  });

  const categoryIcons: { [key: string]: React.ReactNode } = {
    'SAVINGS': <PiggyBank className="w-5 h-5" />,
    'DEBT': <DollarSign className="w-5 h-5" />,
    'INVESTMENT': <TrendingUp className="w-5 h-5" />,
    'PURCHASE': <Gift className="w-5 h-5" />,
    'OTHER': <Target className="w-5 h-5" />,
    'Emergency Fund': <PiggyBank className="w-5 h-5" />,
    'Home': <Home className="w-5 h-5" />,
    'Vehicle': <Car className="w-5 h-5" />,
    'Education': <GraduationCap className="w-5 h-5" />,
    'Travel': <Plane className="w-5 h-5" />,
    'Health': <Heart className="w-5 h-5" />,
    'Gift': <Gift className="w-5 h-5" />,
    'Retirement': <Briefcase className="w-5 h-5" />,
    'Other': <Target className="w-5 h-5" />,
  };

  useEffect(() => {
      text: `User ${user?.username || 'unknown'} viewed goals page`,
      page_name: 'Goals',
      user_id: user?.id,
      timestamp: new Date().toISOString()
    });
    loadGoals();
  }, [user]);

  const loadGoals = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const apiGoals = await goalsService.getGoals();
      
      // Transform API goals to UI format
      const transformedGoals: Goal[] = apiGoals.map(goal => {
        // Calculate monthly contribution
        const today = new Date();
        const targetDate = new Date(goal.target_date);
        const monthsRemaining = Math.max(1, 
          (targetDate.getFullYear() - today.getFullYear()) * 12 + 
          (targetDate.getMonth() - today.getMonth())
        );
        const amountNeeded = Math.max(0, goal.target_amount - goal.current_amount);
        const monthlyContribution = amountNeeded / monthsRemaining;
        
        // Determine risk level
        let riskLevel: Goal['riskLevel'] = 'on-track';
        if (goal.progress_percentage >= 100) {
          riskLevel = 'on-track';
        } else if (goal.days_remaining < 60 && goal.progress_percentage < 50) {
          riskLevel = 'at-risk';
        } else if (monthlyContribution > goal.monthly_target * 1.5) {
          riskLevel = 'at-risk';
        }
        
        // Create milestones
        const milestones = [
          { amount: goal.target_amount * 0.25, description: '25% Complete', reached: goal.progress_percentage >= 25, reachedDate: undefined },
          { amount: goal.target_amount * 0.50, description: '50% Complete', reached: goal.progress_percentage >= 50, reachedDate: undefined },
          { amount: goal.target_amount * 0.75, description: '75% Complete', reached: goal.progress_percentage >= 75, reachedDate: undefined },
          { amount: goal.target_amount, description: 'Goal Achieved!', reached: goal.progress_percentage >= 100, reachedDate: goal.achieved_date },
        ];
        
        return {
          id: goal.id.toString(),
          name: goal.name,
          description: goal.description,
          category: goal.category,
          icon: categoryIcons[goal.category] || categoryIcons['OTHER'],
          targetAmount: goal.target_amount,
          currentAmount: goal.current_amount,
          deadline: goal.target_date,
          createdAt: goal.created_at,
          status: goal.is_achieved ? 'completed' : 'active',
          priority: goal.priority,
          progress: goal.progress_percentage,
          monthlyContribution: monthlyContribution,
          automatedSaving: false,
          milestones,
          projectedCompletion: targetDate.toISOString().split('T')[0],
          riskLevel
        };
      });
      
      setGoals(transformedGoals);
      
      // Calculate summary statistics
      const totalTargetAmount = transformedGoals.reduce((sum, g) => sum + g.targetAmount, 0);
      const totalCurrentAmount = transformedGoals.reduce((sum, g) => sum + g.currentAmount, 0);
      const activeGoals = transformedGoals.filter(g => g.status === 'active');
      const completedGoals = transformedGoals.filter(g => g.status === 'completed');
      const goalsAtRisk = transformedGoals.filter(g => g.riskLevel === 'at-risk');
      
        text: `Goals data loaded: ${transformedGoals.length} total goals, ${activeGoals.length} active, ${completedGoals.length} completed`,
        custom_action: 'goals_data_loaded',
        data: {
          total_goals: transformedGoals.length,
          active_goals: activeGoals.length,
          completed_goals: completedGoals.length,
          goals_at_risk: goalsAtRisk.length,
          total_target_amount: totalTargetAmount,
          total_current_amount: totalCurrentAmount,
          overall_progress: totalTargetAmount > 0 ? (totalCurrentAmount / totalTargetAmount * 100).toFixed(1) : 0,
          categories_used: [...new Set(transformedGoals.map(g => g.category))],
          priorities: {
            high: transformedGoals.filter(g => g.priority === 'HIGH').length,
            medium: transformedGoals.filter(g => g.priority === 'MEDIUM').length,
            low: transformedGoals.filter(g => g.priority === 'LOW').length
          }
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load goals');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateGoal = async () => {
    try {
      if (!goalForm.name || !goalForm.targetAmount || !goalForm.targetDate) {
        showError('Form Incomplete', 'Please fill in all required fields: name, target amount, and target date.');
        return;
      }
      
      const newGoal: GoalCreate = {
        name: goalForm.name,
        description: goalForm.description || undefined,
        target_amount: parseFloat(goalForm.targetAmount),
        target_date: goalForm.targetDate,
        category: goalForm.category,
        priority: goalForm.priority,
        initial_amount: parseFloat(goalForm.initialAmount) || 0
      };
      
      await goalsService.createGoal(newGoal);
      
        text: `User created new ${goalForm.category} goal "${goalForm.name}" with target $${goalForm.targetAmount}`,
        custom_action: 'create_goal',
        data: {
          goal_name: goalForm.name,
          goal_category: goalForm.category,
          target_amount: parseFloat(goalForm.targetAmount),
          initial_amount: parseFloat(goalForm.initialAmount) || 0,
          target_date: goalForm.targetDate,
          priority: goalForm.priority,
          days_to_target: Math.floor((new Date(goalForm.targetDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)),
          existing_goals: goals.length,
          has_description: !!goalForm.description
        }
      });
      
      setShowCreateGoal(false);
      setGoalForm({
        name: '',
        description: '',
        targetAmount: '',
        initialAmount: '0',
        targetDate: '',
        category: 'SAVINGS',
        priority: 'MEDIUM'
      });
      await loadGoals();
    } catch (err) {
      console.error('Failed to create goal:', err);
      showError('Goal Creation Failed', 'Unable to create the goal. Please try again.');
    }
  };
  
  const handleUpdateGoal = async () => {
    if (!selectedGoal) return;
    
    try {
      const updates: GoalUpdate = {
        name: goalForm.name || undefined,
        description: goalForm.description || undefined,
        target_amount: goalForm.targetAmount ? parseFloat(goalForm.targetAmount) : undefined,
        target_date: goalForm.targetDate || undefined,
        category: goalForm.category,
        priority: goalForm.priority
      };
      
      await goalsService.updateGoal(parseInt(selectedGoal.id), updates);
      
        text: `User updated goal "${selectedGoal.name}" -> "${goalForm.name}"`,
        custom_action: 'update_goal',
        data: {
          goal_id: selectedGoal.id,
          old_name: selectedGoal.name,
          new_name: goalForm.name,
          old_target: selectedGoal.targetAmount,
          new_target: goalForm.targetAmount ? parseFloat(goalForm.targetAmount) : selectedGoal.targetAmount,
          old_date: selectedGoal.deadline,
          new_date: goalForm.targetDate || selectedGoal.deadline,
          old_category: selectedGoal.category,
          new_category: goalForm.category,
          old_priority: selectedGoal.priority,
          new_priority: goalForm.priority,
          progress_before_update: selectedGoal.progress,
          current_amount: selectedGoal.currentAmount
        }
      });
      
      setIsEditMode(false);
      setShowGoalDetails(false);
      setSelectedGoal(null);
      await loadGoals();
    } catch (err) {
      console.error('Failed to update goal:', err);
      showError('Goal Update Failed', 'Unable to update the goal. Please try again.');
    }
  };
  
  const handleEditClick = () => {
    if (selectedGoal) {
        text: `User editing goal "${selectedGoal.name}"`,
        custom_action: 'edit_goal_initiated',
        data: {
          goal_id: selectedGoal.id,
          goal_name: selectedGoal.name,
          current_progress: selectedGoal.progress,
          current_amount: selectedGoal.currentAmount,
          target_amount: selectedGoal.targetAmount,
          risk_level: selectedGoal.riskLevel,
          days_to_deadline: Math.floor((new Date(selectedGoal.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
        }
      });
      setGoalForm({
        name: selectedGoal.name,
        description: selectedGoal.description || '',
        targetAmount: selectedGoal.targetAmount.toString(),
        initialAmount: selectedGoal.currentAmount.toString(),
        targetDate: selectedGoal.deadline,
        category: selectedGoal.category,
        priority: selectedGoal.priority
      });
      setIsEditMode(true);
    }
  };

  const categories = ['all', 'SAVINGS', 'DEBT', 'INVESTMENT', 'PURCHASE', 'OTHER'];
  const statuses = ['all', 'active', 'completed', 'paused'];

  const filteredGoals = goals.filter(goal => {
    const categoryMatch = filterCategory === 'all' || goal.category === filterCategory;
    const statusMatch = filterStatus === 'all' || goal.status === filterStatus;
    return categoryMatch && statusMatch;
  }).sort((a, b) => {
    switch (sortBy) {
      case 'deadline':
        return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
      case 'progress':
        return b.progress - a.progress;
      case 'amount':
        return b.targetAmount - a.targetAmount;
      default:
        return 0;
    }
  });

  const totalSaved = goals.reduce((sum, goal) => sum + goal.currentAmount, 0);
  const totalTarget = goals.reduce((sum, goal) => sum + goal.targetAmount, 0);
  const activeGoals = goals.filter(g => g.status === 'active').length;
  const completedGoals = goals.filter(g => g.status === 'completed').length;

  const handleGoalClick = (goal: Goal) => {
      text: `User selected goal "${goal.name}" with ${goal.progress.toFixed(0)}% progress`,
      custom_action: 'select_goal',
      data: {
        goal_id: goal.id,
        goal_name: goal.name,
        goal_category: goal.category,
        target_amount: goal.targetAmount,
        current_amount: goal.currentAmount,
        progress_percentage: goal.progress,
        days_remaining: Math.floor((new Date(goal.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)),
        risk_level: goal.riskLevel,
        status: goal.status,
        priority: goal.priority
      }
    });
    setSelectedGoal(goal);
    setShowGoalDetails(true);
  };

  if (isLoading) {
    return (
      <div className="h-[calc(100vh-4rem)]">
        <div className="flex items-center justify-center h-96">
          <div className="text-[var(--text-2)]">Loading goals...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card variant="error" className="p-8 text-center">
          <AlertCircle className="w-12 h-12 text-[var(--primary-red)] mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-[var(--text-1)] mb-2">
            Unable to Load Goals
          </h2>
          <p className="text-[var(--text-2)] mb-6">{error}</p>
          <Button onClick={loadGoals} variant="primary">
            Try Again
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[var(--text-1)]">
              Financial Goals
            </h1>
            <p className="text-[var(--text-2)] mt-2">
              Set and track your savings goals to achieve financial milestones
            </p>
          </div>
          
          <Button
            variant="primary"
            icon={<Plus size={18} />}
            onClick={() => {
                text: `User opening create goal modal with ${goals.filter(g => g.status === 'active').length} active goals`,
                custom_action: 'open_create_goal_modal',
                data: {
                  existing_goals_count: goals.length,
                  active_goals_count: goals.filter(g => g.status === 'active').length,
                  completed_goals_count: goals.filter(g => g.status === 'completed').length,
                  total_target_amount: goals.reduce((sum, g) => sum + g.targetAmount, 0),
                  total_current_amount: goals.reduce((sum, g) => sum + g.currentAmount, 0)
                }
              });
              setShowCreateGoal(true);
            }}
            className="mt-4 md:mt-0"
          >
            Create Goal
          </Button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card variant="default" className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-2)]">Total Saved</p>
                <p className="text-2xl font-bold text-[var(--text-1)]">
                  ${totalSaved.toLocaleString()}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-[var(--primary-emerald)] opacity-20" />
            </div>
          </Card>

          <Card variant="default" className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-2)]">Target Amount</p>
                <p className="text-2xl font-bold text-[var(--text-1)]">
                  ${totalTarget.toLocaleString()}
                </p>
              </div>
              <Target className="w-8 h-8 text-[var(--primary-blue)] opacity-20" />
            </div>
          </Card>

          <Card variant="default" className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-2)]">Active Goals</p>
                <p className="text-2xl font-bold text-[var(--text-1)]">
                  {activeGoals}
                </p>
              </div>
              <Clock className="w-8 h-8 text-[var(--primary-amber)] opacity-20" />
            </div>
          </Card>

          <Card variant="default" className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-2)]">Completed</p>
                <p className="text-2xl font-bold text-[var(--primary-emerald)]">
                  {completedGoals}
                </p>
              </div>
              <Trophy className="w-8 h-8 text-[var(--primary-emerald)] opacity-20" />
            </div>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          <Dropdown
            items={categories.map(cat => ({ 
              value: cat, 
              label: cat === 'all' ? 'All Categories' : 
                     cat === 'SAVINGS' ? 'Savings' :
                     cat === 'DEBT' ? 'Debt Payoff' :
                     cat === 'INVESTMENT' ? 'Investment' :
                     cat === 'PURCHASE' ? 'Purchase' :
                     cat === 'OTHER' ? 'Other' : cat
            }))}
            value={filterCategory}
            onChange={(value) => {
              const oldCategory = filterCategory;
              setFilterCategory(value);
                text: `User filtered goals by category: ${value === 'all' ? 'All Categories' : value}`,
                filter_type: 'category',
                filter_value: value,
                data: {
                  old_category: oldCategory,
                  new_category: value,
                  goals_before_filter: goals.length,
                  goals_after_filter: goals.filter(g => value === 'all' || g.category === value).length
                }
              });
            }}
            placeholder="Category"
          />
          
          <Dropdown
            items={statuses.map(status => ({ 
              value: status, 
              label: status === 'all' ? 'All Status' : status.charAt(0).toUpperCase() + status.slice(1) 
            }))}
            value={filterStatus}
            onChange={(value) => {
              const oldStatus = filterStatus;
              setFilterStatus(value);
                text: `User filtered goals by status: ${value === 'all' ? 'All Status' : value}`,
                filter_type: 'status',
                filter_value: value,
                data: {
                  old_status: oldStatus,
                  new_status: value,
                  goals_before_filter: goals.length,
                  goals_after_filter: goals.filter(g => value === 'all' || g.status === value).length
                }
              });
            }}
            placeholder="Status"
          />
          
          <Dropdown
            items={[
              { value: 'deadline', label: 'Sort by Deadline' },
              { value: 'progress', label: 'Sort by Progress' },
              { value: 'amount', label: 'Sort by Amount' },
            ]}
            value={sortBy}
            onChange={(value) => {
              const oldSort = sortBy;
              setSortBy(value as 'deadline' | 'progress' | 'amount');
                text: `User sorted goals by ${value}`,
                sort_field: value,
                sort_order: 'asc',
                data: {
                  old_sort: oldSort,
                  new_sort: value,
                  goals_count: filteredGoals.length
                }
              });
            }}
            placeholder="Sort by"
          />
        </div>

        {/* Goals Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredGoals.map((goal, index) => (
            <motion.div
              key={goal.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <GoalCard
                goal={goal}
                onClick={() => handleGoalClick(goal)}
              />
            </motion.div>
          ))}

          {filteredGoals.length === 0 && (
            <div className="col-span-full text-center py-12">
              <Target className="w-12 h-12 mx-auto mb-4 text-[var(--text-2)] opacity-50" />
              <p className="text-[var(--text-2)]">No goals found</p>
              <p className="text-sm text-[var(--text-2)] mt-2">
                Try adjusting your filters or create a new goal
              </p>
            </div>
          )}
        </div>
      {/* Create Goal Modal */}
      <Modal
        isOpen={showCreateGoal}
        onClose={() => {
          setShowCreateGoal(false);
          setGoalForm({
            name: '',
            description: '',
            targetAmount: '',
            initialAmount: '0',
            targetDate: '',
            category: 'SAVINGS',
            priority: 'MEDIUM'
          });
        }}
        title="Create Financial Goal"
        size="lg"
      >
        <div className="space-y-4">
          <Input
            label="Goal Name"
            type="text"
            placeholder="e.g., Emergency Fund"
            value={goalForm.name}
            onChange={(e) => {
              setGoalForm({ ...goalForm, name: e.target.value });
                text: `User entered goal name: "${e.target.value}"`,
                field_name: 'goal_name',
                field_value: e.target.value,
                form_type: 'create_goal'
              });
            }}
            required
          />
          
          <Input
            label="Description (Optional)"
            type="text"
            placeholder="e.g., Save for 6 months of expenses"
            value={goalForm.description}
            onChange={(e) => {
              setGoalForm({ ...goalForm, description: e.target.value });
                text: `User entered goal description: "${e.target.value}"`,
                field_name: 'goal_description',
                field_value: e.target.value,
                form_type: 'create_goal'
              });
            }}
          />
          
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Target Amount"
              type="number"
              placeholder="0.00"
              value={goalForm.targetAmount}
              onChange={(e) => {
                setGoalForm({ ...goalForm, targetAmount: e.target.value });
                  text: `User set target amount: $${e.target.value}`,
                  field_name: 'target_amount',
                  field_value: e.target.value,
                  form_type: 'create_goal',
                  data: {
                    amount: parseFloat(e.target.value) || 0,
                    is_valid: !isNaN(parseFloat(e.target.value)) && parseFloat(e.target.value) > 0
                  }
                });
              }}
              icon={<DollarSign size={18} />}
              required
            />
            
            <Input
              label="Initial Amount"
              type="number"
              placeholder="0.00"
              value={goalForm.initialAmount}
              onChange={(e) => {
                setGoalForm({ ...goalForm, initialAmount: e.target.value });
                  text: `User set initial amount: $${e.target.value}`,
                  field_name: 'initial_amount',
                  field_value: e.target.value,
                  form_type: 'create_goal',
                  data: {
                    amount: parseFloat(e.target.value) || 0,
                    percentage_of_target: goalForm.targetAmount ? ((parseFloat(e.target.value) || 0) / parseFloat(goalForm.targetAmount) * 100).toFixed(1) : 0
                  }
                });
              }}
              icon={<DollarSign size={18} />}
            />
          </div>
          
          <DatePicker
            label="Target Date"
            value={goalForm.targetDate}
            onChange={(value) => {
              setGoalForm({ ...goalForm, targetDate: value });
              const daysToTarget = Math.floor((new Date(value).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
                text: `User selected target date: ${value} (${daysToTarget} days from now)`,
                field_name: 'target_date',
                field_value: value,
                form_type: 'create_goal',
                data: {
                  date: value,
                  days_to_target: daysToTarget,
                  months_to_target: Math.floor(daysToTarget / 30)
                }
              });
            }}
            minDate={new Date().toISOString().split('T')[0]}
            required
          />
          
          <div className="grid grid-cols-2 gap-4">
            <Dropdown
              label="Category"
              items={[
                { value: 'SAVINGS', label: 'Savings' },
                { value: 'DEBT', label: 'Debt Payoff' },
                { value: 'INVESTMENT', label: 'Investment' },
                { value: 'PURCHASE', label: 'Purchase' },
                { value: 'OTHER', label: 'Other' },
              ]}
              value={goalForm.category}
              onChange={(value) => {
                setGoalForm({ ...goalForm, category: value as GoalCreate['category'] });
                  text: `User selected goal category: ${value}`,
                  field_name: 'goal_category',
                  field_value: value,
                  form_type: 'create_goal'
                });
              }}
              placeholder="Select category"
            />
            
            <Dropdown
              label="Priority"
              items={[
                { value: 'LOW', label: 'Low' },
                { value: 'MEDIUM', label: 'Medium' },
                { value: 'HIGH', label: 'High' },
              ]}
              value={goalForm.priority || 'MEDIUM'}
              onChange={(value) => {
                setGoalForm({ ...goalForm, priority: value as GoalCreate['priority'] });
                  text: `User selected goal priority: ${value}`,
                  field_name: 'goal_priority',  
                  field_value: value,
                  form_type: 'create_goal'
                });
              }}
              placeholder="Select priority"
            />
          </div>
          
          <div className="flex gap-3 pt-4">
            <Button
              variant="secondary"
              fullWidth
              onClick={() => {
                  text: `User cancelled goal creation with form data: name="${goalForm.name}", amount=$${goalForm.targetAmount || '0'}`,
                  custom_action: 'cancel_create_goal',
                  data: {
                    had_name: !!goalForm.name,
                    had_amount: !!goalForm.targetAmount,
                    had_date: !!goalForm.targetDate,
                    form_completion: {
                      name: !!goalForm.name,
                      description: !!goalForm.description,
                      target_amount: !!goalForm.targetAmount,
                      initial_amount: goalForm.initialAmount !== '0',
                      target_date: !!goalForm.targetDate,
                      category_changed: goalForm.category !== 'SAVINGS',
                      priority_changed: goalForm.priority !== 'MEDIUM'
                    }
                  }
                });
                setShowCreateGoal(false);
                setGoalForm({
                  name: '',
                  description: '',
                  targetAmount: '',
                  initialAmount: '0',
                  targetDate: '',
                  category: 'SAVINGS',
                  priority: 'MEDIUM'
                });
              }}
            >
              Cancel
            </Button>
            <Button 
              variant="primary" 
              fullWidth
              onClick={() => {
                  text: `User clicked create goal with "${goalForm.name}" target $${goalForm.targetAmount}`,
                  custom_action: 'submit_create_goal',
                  data: {
                    goal_name: goalForm.name,
                    target_amount: parseFloat(goalForm.targetAmount) || 0,
                    initial_amount: parseFloat(goalForm.initialAmount) || 0,
                    category: goalForm.category,
                    priority: goalForm.priority,
                    target_date: goalForm.targetDate,
                    has_description: !!goalForm.description,
                    days_to_target: goalForm.targetDate ? Math.floor((new Date(goalForm.targetDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)) : 0
                  }
                });
                handleCreateGoal();
              }}
            >
              Create Goal
            </Button>
          </div>
        </div>
      </Modal>

      {/* Goal Details Modal */}
      {selectedGoal && (
        <Modal
          isOpen={showGoalDetails}
          onClose={() => {
              text: `User closed goal details modal for "${selectedGoal.name}"`,
              custom_action: 'close_goal_details',
              data: {
                goal_id: selectedGoal.id,
                goal_name: selectedGoal.name,
                was_editing: isEditMode,
                goal_progress: selectedGoal.progress,
                goal_status: selectedGoal.status
              }
            });
            setShowGoalDetails(false);
            setSelectedGoal(null);
            setIsEditMode(false);
          }}
          title={isEditMode ? 'Edit Goal' : selectedGoal.name}
          size="xl"
        >
          <div className="space-y-6">
            {isEditMode ? (
              // Edit Mode Form
              <div className="space-y-4">
                <Input
                  label="Goal Name"
                  type="text"
                  value={goalForm.name}
                  onChange={(e) => setGoalForm({ ...goalForm, name: e.target.value })}
                  required
                />
                
                <Input
                  label="Description"
                  type="text"
                  value={goalForm.description}
                  onChange={(e) => setGoalForm({ ...goalForm, description: e.target.value })}
                />
                
                <Input
                  label="Target Amount"
                  type="number"
                  value={goalForm.targetAmount}
                  onChange={(e) => setGoalForm({ ...goalForm, targetAmount: e.target.value })}
                  icon={<DollarSign size={18} />}
                  required
                />
                
                <DatePicker
                  label="Target Date"
                  value={goalForm.targetDate}
                  onChange={(value) => setGoalForm({ ...goalForm, targetDate: value })}
                  minDate={new Date().toISOString().split('T')[0]}
                  required
                />
                
                <div className="grid grid-cols-2 gap-4">
                  <Dropdown
                    label="Category"
                    items={[
                      { value: 'SAVINGS', label: 'Savings' },
                      { value: 'DEBT', label: 'Debt Payoff' },
                      { value: 'INVESTMENT', label: 'Investment' },
                      { value: 'PURCHASE', label: 'Purchase' },
                      { value: 'OTHER', label: 'Other' },
                    ]}
                    value={goalForm.category}
                    onChange={(value) => setGoalForm({ ...goalForm, category: value as GoalCreate['category'] })}
                  />
                  
                  <Dropdown
                    label="Priority"
                    items={[
                      { value: 'LOW', label: 'Low' },
                      { value: 'MEDIUM', label: 'Medium' },
                      { value: 'HIGH', label: 'High' },
                    ]}
                    value={goalForm.priority}
                    onChange={(value) => setGoalForm({ ...goalForm, priority: value as GoalCreate['priority'] })}
                  />
                </div>
                
                <div className="flex gap-3 pt-4">
                  <Button
                    variant="secondary"
                    fullWidth
                    onClick={() => {
                        text: `User cancelled editing goal "${selectedGoal.name}"`,
                        custom_action: 'cancel_edit_goal',
                        data: {
                          goal_id: selectedGoal.id,
                          goal_name: selectedGoal.name,
                          had_changes: goalForm.name !== selectedGoal.name || 
                                      goalForm.targetAmount !== selectedGoal.targetAmount.toString() ||
                                      goalForm.targetDate !== selectedGoal.deadline ||
                                      goalForm.category !== selectedGoal.category ||
                                      goalForm.priority !== selectedGoal.priority
                        }
                      });
                      setIsEditMode(false);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button 
                    variant="primary" 
                    fullWidth
                    onClick={() => {
                        text: `User clicked update goal for "${selectedGoal.name}"`,
                        custom_action: 'submit_update_goal',
                        data: {
                          goal_id: selectedGoal.id,
                          old_values: {
                            name: selectedGoal.name,
                            target_amount: selectedGoal.targetAmount,
                            target_date: selectedGoal.deadline,
                            category: selectedGoal.category,
                            priority: selectedGoal.priority
                          },
                          new_values: {
                            name: goalForm.name,
                            target_amount: parseFloat(goalForm.targetAmount) || selectedGoal.targetAmount,
                            target_date: goalForm.targetDate,
                            category: goalForm.category,
                            priority: goalForm.priority
                          }
                        }
                      });
                      handleUpdateGoal();
                    }}
                  >
                    Update Goal
                  </Button>
                </div>
              </div>
            ) : (
              // View Mode
              <>
                <GoalProgress goal={selectedGoal} />
                <GoalMilestones goal={selectedGoal} />
                
                <div className="flex gap-3 pt-4">
                  <Button 
                    variant="primary" 
                    fullWidth
                    onClick={handleEditClick}
                  >
                    Edit Goal
                  </Button>
                  <Button 
                    variant="secondary" 
                    fullWidth
                    onClick={() => {
                      const newState = !selectedGoal.automatedSaving;
                        text: `User ${newState ? 'enabled' : 'paused'} auto-save for goal "${selectedGoal.name}"`,
                        toggle_type: 'auto_save',
                        toggle_state: newState,
                        data: {
                          goal_id: selectedGoal.id,
                          goal_name: selectedGoal.name,
                          goal_progress: selectedGoal.progress,
                          monthly_contribution: selectedGoal.monthlyContribution,
                          days_to_deadline: Math.floor((new Date(selectedGoal.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
                        }
                      });
                      // Note: Actual implementation would update the goal here
                    }}
                  >
                    {selectedGoal.automatedSaving ? 'Pause Auto-Save' : 'Enable Auto-Save'}
                  </Button>
                </div>
              </>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
