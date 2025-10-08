import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ChevronRight, ChevronLeft } from 'lucide-react';
import Button from '@/components/ui/Button';

interface DemoStep {
  id: string;
  title: string;
  description: string;
  element?: string;
  action?: () => void;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  steps: DemoStep[];
}

interface DemoModeContextType {
  isDemoMode: boolean;
  toggleDemoMode: () => void;
  startDemo: (scenarioId: string) => void;
  nextStep: () => void;
  previousStep: () => void;
  skipDemo: () => void;
  currentScenario: DemoScenario | null;
  currentStep: number;
  isPlaying: boolean;
  scenarios: DemoScenario[];
}

const DemoModeContext = createContext<DemoModeContextType | undefined>(undefined);

const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'quick-tour',
    name: 'Quick Tour',
    description: 'Get familiar with the main features',
    steps: [
      {
        id: 'welcome',
        title: 'Welcome to Your Finance Hub',
        description: 'This is your personal dashboard where you can manage all your finances in one place.',
      },
      {
        id: 'accounts',
        title: 'Your Accounts',
        description: 'View all your accounts at a glance. Click on any account for detailed information.',
        element: '.account-cards',
      },
      {
        id: 'quick-actions',
        title: 'Quick Actions',
        description: 'Perform common tasks like transfers, payments, and deposits with just one tap.',
        element: '.quick-actions',
      },
      {
        id: 'transactions',
        title: 'Recent Transactions',
        description: 'Track your spending and income. Tap any transaction for more details.',
        element: '.recent-transactions',
      },
      {
        id: 'spending',
        title: 'Spending Insights',
        description: 'Visualize where your money goes with interactive charts and analytics.',
        element: '.spending-overview',
      },
    ],
  },
  {
    id: 'make-payment',
    name: 'Make a Payment',
    description: 'Learn how to send money to friends or pay bills',
    steps: [
      {
        id: 'start-payment',
        title: 'Starting a Payment',
        description: 'Click the "Send Money" button in Quick Actions to begin.',
        element: '.quick-action-send',
      },
      {
        id: 'select-recipient',
        title: 'Choose Recipient',
        description: 'Select from your contacts or enter a new recipient.',
      },
      {
        id: 'enter-amount',
        title: 'Enter Amount',
        description: 'Type the amount you want to send and add an optional note.',
      },
      {
        id: 'confirm-payment',
        title: 'Confirm & Send',
        description: 'Review the details and slide to confirm your payment.',
      },
    ],
  },
  {
    id: 'setup-budget',
    name: 'Set Up a Budget',
    description: 'Create and manage your monthly budgets',
    steps: [
      {
        id: 'navigate-budget',
        title: 'Go to Budgets',
        description: 'Click on "Budget" in the navigation menu.',
      },
      {
        id: 'create-budget',
        title: 'Create New Budget',
        description: 'Click "Create Budget" to set up a new spending category.',
      },
      {
        id: 'set-limits',
        title: 'Set Spending Limits',
        description: 'Define your monthly spending limit for each category.',
      },
      {
        id: 'track-progress',
        title: 'Track Your Progress',
        description: 'Monitor your spending against your budget throughout the month.',
      },
    ],
  },
];

export const DemoModeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [currentScenario, setCurrentScenario] = useState<DemoScenario | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    // Check if it's the first visit
    const hasVisited = localStorage.getItem('has_visited');
    if (!hasVisited) {
      setIsDemoMode(true);
      localStorage.setItem('has_visited', 'true');
    }
  }, []);

  const toggleDemoMode = () => {
    setIsDemoMode(!isDemoMode);
    if (!isDemoMode) {
      setCurrentScenario(null);
      setCurrentStep(0);
      setIsPlaying(false);
    }
  };

  const startDemo = (scenarioId: string) => {
    const scenario = DEMO_SCENARIOS.find(s => s.id === scenarioId);
    if (scenario) {
      setCurrentScenario(scenario);
      setCurrentStep(0);
      setIsPlaying(true);
      setIsDemoMode(true);
    }
  };

  const nextStep = () => {
    if (currentScenario && currentStep < currentScenario.steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      skipDemo();
    }
  };

  const previousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const skipDemo = () => {
    setIsPlaying(false);
    setCurrentScenario(null);
    setCurrentStep(0);
  };

  const value: DemoModeContextType = {
    isDemoMode,
    toggleDemoMode,
    startDemo,
    nextStep,
    previousStep,
    skipDemo,
    currentScenario,
    currentStep,
    isPlaying,
    scenarios: DEMO_SCENARIOS,
  };

  return (
    <DemoModeContext.Provider value={value}>
      {children}
      <DemoTooltip />
      <DemoModeIndicator />
    </DemoModeContext.Provider>
  );
};

export const useDemoMode = () => {
  const context = useContext(DemoModeContext);
  if (context === undefined) {
    throw new Error('useDemoMode must be used within a DemoModeProvider');
  }
  return context;
};

// Demo Tooltip Component
const DemoTooltip: React.FC = () => {
  const { currentScenario, currentStep, isPlaying, nextStep, previousStep, skipDemo } = useDemoMode();

  if (!isPlaying || !currentScenario) return null;

  const step = currentScenario.steps[currentStep];
  const progress = ((currentStep + 1) / currentScenario.steps.length) * 100;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="fixed inset-x-4 bottom-24 z-[100] max-w-md mx-auto md:inset-x-auto md:right-8 md:left-auto md:bottom-8"
      >
        <Card variant="prominent" className="shadow-2xl">
          <div className="p-6">
            {/* Progress bar */}
            <div className="h-1 bg-[rgba(var(--glass-rgb),0.2)] rounded-full mb-4 overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-[var(--primary-blue)] to-[var(--primary-indigo)]"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ type: 'spring', stiffness: 400, damping: 40 }}
              />
            </div>

            {/* Content */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-[var(--text-1)] mb-2 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[var(--primary-blue)]" />
                {step.title}
              </h3>
              <p className="text-sm text-[var(--text-2)]">{step.description}</p>
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                size="sm"
                onClick={skipDemo}
                className="text-[var(--text-2)]"
              >
                Skip tour
              </Button>

              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={previousStep}
                  disabled={currentStep === 0}
                  className="p-2"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>

                <span className="text-xs text-[var(--text-2)] px-2">
                  {currentStep + 1} / {currentScenario.steps.length}
                </span>

                <Button
                  variant="primary"
                  size="sm"
                  onClick={nextStep}
                  className="flex items-center gap-1"
                >
                  {currentStep === currentScenario.steps.length - 1 ? 'Finish' : 'Next'}
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>
    </AnimatePresence>
  );
};

// Demo Mode Indicator - Hidden as requested
const DemoModeIndicator: React.FC = () => {
  // Always return null to hide the demo mode indicator
  return null;
};

// Card component - theme-aware version
const Card: React.FC<{ variant?: string; className?: string; children: ReactNode }> = ({ 
  variant = 'default', 
  className = '', 
  children 
}) => {
  const variantClasses = variant === 'prominent' 
    ? 'bg-[rgba(var(--glass-rgb),var(--glass-alpha-high))] backdrop-blur-xl border border-[var(--glass-border-prominent)] shadow-xl' 
    : 'bg-[rgba(var(--glass-rgb),var(--glass-alpha))] backdrop-blur-lg border border-[var(--glass-border)]';
    
  return (
    <div className={`rounded-xl p-4 ${variantClasses} ${className}`}>
      {children}
    </div>
  );
};