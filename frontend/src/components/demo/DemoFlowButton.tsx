import React from 'react';
import { motion } from 'framer-motion';
import { Play, Sparkles } from 'lucide-react';
import Button from '../ui/Button';
import { useDemoMode } from '@/contexts/DemoModeContext';

interface DemoFlowButtonProps {
  scenarioId: 'quick-tour' | 'make-payment' | 'setup-budget';
  className?: string;
  variant?: 'floating' | 'inline';
}

export const DemoFlowButton: React.FC<DemoFlowButtonProps> = ({
  scenarioId,
  className = '',
  variant = 'floating',
}) => {
  const { startDemo, isDemoMode, scenarios } = useDemoMode();
  
  const scenario = scenarios.find(s => s.id === scenarioId);
  
  if (!scenario || !isDemoMode) return null;

  if (variant === 'floating') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={`fixed bottom-24 right-4 z-40 ${className}`}
      >
        <Button
          variant="primary"
          size="lg"
          icon={<Play className="w-5 h-5" />}
          onClick={() => startDemo(scenarioId)}
          className="shadow-lg flex items-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          Try Demo: {scenario.name}
        </Button>
      </motion.div>
    );
  }

  return (
    <Button
      variant="secondary"
      size="sm"
      icon={<Play className="w-4 h-4" />}
      onClick={() => startDemo(scenarioId)}
      className={`flex items-center gap-2 ${className}`}
    >
      <Sparkles className="w-4 h-4" />
      Demo
    </Button>
  );
};

// Demo scenario cards for selection
export const DemoScenarioSelector: React.FC<{
  onClose?: () => void;
}> = ({ onClose }) => {
  const { scenarios, startDemo } = useDemoMode();

  return (
    <div className="space-y-4 p-4">
      <h3 className="text-lg font-semibold text-[var(--text-1)] mb-4">
        Choose a Demo Scenario
      </h3>
      
      {scenarios.map((scenario) => (
        <motion.div
          key={scenario.id}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <button
            onClick={() => {
              startDemo(scenario.id);
              onClose?.();
            }}
            className="w-full p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.1)] hover:bg-[rgba(var(--glass-rgb),0.2)] transition-colors text-left"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-[var(--primary-blue)] bg-opacity-20">
                <Sparkles className="w-5 h-5 text-[var(--primary-blue)]" />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-[var(--text-1)] mb-1">
                  {scenario.name}
                </h4>
                <p className="text-sm text-[var(--text-2)]">
                  {scenario.description}
                </p>
                <p className="text-xs text-[var(--text-2)] mt-2">
                  {scenario.steps.length} steps • ~2 min
                </p>
              </div>
              <Play className="w-5 h-5 text-[var(--text-2)]" />
            </div>
          </button>
        </motion.div>
      ))}
    </div>
  );
};

export default DemoFlowButton;