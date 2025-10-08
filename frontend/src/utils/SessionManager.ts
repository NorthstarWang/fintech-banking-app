import { EventEmitter } from 'events';

export interface SessionConfig {
  timeout: number; // in milliseconds
  warningTime: number; // time before timeout to show warning (in milliseconds)
  checkInterval: number; // how often to check for timeout (in milliseconds)
  storageKey: string;
  activityEvents: string[];
}

export interface SessionState {
  lastActivity: number;
  isActive: boolean;
  timeRemaining: number;
  showWarning: boolean;
}

export class SessionManager extends EventEmitter {
  private config: SessionConfig;
  private lastActivity: number;
  private checkTimer: NodeJS.Timeout | null = null;
  private warningTimer: NodeJS.Timeout | null = null;
  private activityHandler: () => void;

  constructor(config: Partial<SessionConfig> = {}) {
    super();
    
    this.config = {
      timeout: 15 * 60 * 1000, // 15 minutes
      warningTime: 2 * 60 * 1000, // 2 minutes
      checkInterval: 1000, // 1 second
      storageKey: 'session_last_activity',
      activityEvents: ['mousedown', 'keypress', 'scroll', 'touchstart', 'click'],
      ...config
    };

    this.lastActivity = Date.now();
    this.activityHandler = this.updateActivity.bind(this);
  }

  /**
   * Start monitoring session activity
   */
  start(): void {
    // Load last activity from storage
    const stored = localStorage.getItem(this.config.storageKey);
    if (stored) {
      this.lastActivity = parseInt(stored, 10);
    } else {
      this.updateActivity();
    }

    // Start activity listeners
    this.config.activityEvents.forEach(event => {
      window.addEventListener(event, this.activityHandler);
    });

    // Start checking for timeout
    this.checkTimer = setInterval(() => {
      this.checkTimeout();
    }, this.config.checkInterval);

    // Start warning timer
    this.scheduleWarning();

    this.emit('start');
  }

  /**
   * Stop monitoring session activity
   */
  stop(): void {
    // Remove activity listeners
    this.config.activityEvents.forEach(event => {
      window.removeEventListener(event, this.activityHandler);
    });

    // Clear timers
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
    }

    if (this.warningTimer) {
      clearTimeout(this.warningTimer);
      this.warningTimer = null;
    }

    this.emit('stop');
  }

  /**
   * Reset the session timer
   */
  reset(): void {
    this.updateActivity();
    this.emit('reset');
  }

  /**
   * Extend the session by a specific amount
   */
  extend(milliseconds: number): void {
    this.lastActivity = Date.now() - (this.config.timeout - milliseconds);
    this.saveActivity();
    this.scheduleWarning();
    this.emit('extend', milliseconds);
  }

  /**
   * Get current session state
   */
  getState(): SessionState {
    const now = Date.now();
    const elapsed = now - this.lastActivity;
    const timeRemaining = Math.max(0, this.config.timeout - elapsed);
    const showWarning = timeRemaining > 0 && timeRemaining <= this.config.warningTime;

    return {
      lastActivity: this.lastActivity,
      isActive: timeRemaining > 0,
      timeRemaining,
      showWarning
    };
  }

  /**
   * Get formatted time remaining
   */
  getFormattedTimeRemaining(): string {
    const { timeRemaining } = this.getState();
    const minutes = Math.floor(timeRemaining / 60000);
    const seconds = Math.floor((timeRemaining % 60000) / 1000);
    
    if (minutes > 0) {
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${seconds}s`;
  }

  /**
   * Update activity timestamp
   */
  private updateActivity(): void {
    const now = Date.now();
    const state = this.getState();
    
    // Only update if session is still active
    if (state.isActive) {
      this.lastActivity = now;
      this.saveActivity();
      this.scheduleWarning();
      this.emit('activity');
    }
  }

  /**
   * Save activity to storage
   */
  private saveActivity(): void {
    localStorage.setItem(this.config.storageKey, this.lastActivity.toString());
  }

  /**
   * Check for timeout
   */
  private checkTimeout(): void {
    const state = this.getState();
    
    if (!state.isActive) {
      this.handleTimeout();
    } else {
      this.emit('tick', state);
    }
  }

  /**
   * Schedule warning notification
   */
  private scheduleWarning(): void {
    if (this.warningTimer) {
      clearTimeout(this.warningTimer);
    }

    const timeUntilWarning = this.config.timeout - this.config.warningTime;
    
    this.warningTimer = setTimeout(() => {
      const state = this.getState();
      if (state.isActive && state.showWarning) {
        this.emit('warning', state);
      }
    }, timeUntilWarning);
  }

  /**
   * Handle session timeout
   */
  private handleTimeout(): void {
    this.stop();
    localStorage.removeItem(this.config.storageKey);
    this.emit('timeout');
  }

  /**
   * Check if another tab is active
   */
  isAnotherTabActive(): boolean {
    const stored = localStorage.getItem(this.config.storageKey);
    if (!stored) return false;
    
    const storedTime = parseInt(stored, 10);
    const timeSinceStored = Date.now() - storedTime;
    
    // If another tab updated within 2 seconds, it's active
    return timeSinceStored < 2000 && storedTime > this.lastActivity;
  }

  /**
   * Static method to clear all session data
   */
  static clearAllSessions(): void {
    const keys = Object.keys(localStorage).filter(key => 
      key.includes('session_') || key.includes('auth_')
    );
    
    keys.forEach(key => localStorage.removeItem(key));
  }
}

// Singleton instance
let sessionManagerInstance: SessionManager | null = null;

export function getSessionManager(config?: Partial<SessionConfig>): SessionManager {
  if (!sessionManagerInstance) {
    sessionManagerInstance = new SessionManager(config);
  }
  return sessionManagerInstance;
}

// React hook for session management
import { useState, useEffect } from 'react';

export function useSessionManager(config?: Partial<SessionConfig>) {
  const [state, setState] = useState<SessionState>({
    lastActivity: Date.now(),
    isActive: true,
    timeRemaining: config?.timeout || 15 * 60 * 1000,
    showWarning: false
  });

  useEffect(() => {
    const manager = getSessionManager(config);
    
    const handleTick = (newState: SessionState) => {
      setState(newState);
    };

    const handleTimeout = () => {
      setState(prev => ({ ...prev, isActive: false, timeRemaining: 0 }));
    };

    const handleWarning = (newState: SessionState) => {
      setState(newState);
    };

    manager.on('tick', handleTick);
    manager.on('timeout', handleTimeout);
    manager.on('warning', handleWarning);
    
    manager.start();

    return () => {
      manager.off('tick', handleTick);
      manager.off('timeout', handleTimeout);
      manager.off('warning', handleWarning);
    };
  }, [config]);

  return {
    ...state,
    extend: (ms: number) => getSessionManager().extend(ms),
    reset: () => getSessionManager().reset(),
    getFormattedTime: () => getSessionManager().getFormattedTimeRemaining()
  };
}