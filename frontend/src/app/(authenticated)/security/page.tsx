'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Shield,
  Lock,
  Smartphone,
  Key,
  Fingerprint,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  Monitor,
  Globe,
  Clock,
  MapPin,
  Activity,
  Settings,
  Download,
  RefreshCw,
  LogOut,
  Zap,
  ShieldCheck,
  UserX,
  AlertCircle,
  ChevronRight
} from 'lucide-react';
import Card, { CardHeader, CardBody } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import TwoFactorInput from '@/components/ui/TwoFactorInput';
import BiometricAuth from '@/components/ui/BiometricAuth';
import SlideToConfirm from '@/components/ui/SlideToConfirm';
import { useAuth } from '@/contexts/AuthContext';
import { securityApi } from '@/lib/api';
import { checkPasswordStrength } from '@/utils/security';
import { notificationService } from '@/services/notificationService';

interface SecurityEvent {
  id: string;
  type: 'login' | 'password_change' | 'settings_change' | 'suspicious_activity';
  description: string;
  timestamp: string;
  location: string;
  device: string;
  ip: string;
  status: 'success' | 'failed' | 'warning';
}

interface LoginSession {
  id: string;
  device: string;
  browser: string;
  location: string;
  ip: string;
  lastActive: string;
  current: boolean;
}

export default function SecurityPage() {
  const { user } = useAuth();
  const [securityScore, setSecurityScore] = useState(75);
  const [showEnableTwoFactorModal, setShowEnableTwoFactorModal] = useState(false);
  const [showDisableTwoFactorModal, setShowDisableTwoFactorModal] = useState(false);
  const [showSessionDetailsModal, setShowSessionDetailsModal] = useState(false);
  const [selectedSession, setSelectedSession] = useState<LoginSession | null>(null);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTwoFactorMethod, setSelectedTwoFactorMethod] = useState<'authenticator' | 'sms' | 'email' | null>(null);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [setupStartTime, setSetupStartTime] = useState<number>(0);
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [securityEvents] = useState<SecurityEvent[]>([
    {
      id: '1',
      type: 'login',
      description: 'Successful login',
      timestamp: '2025-06-16 14:32:00',
      location: 'New York, NY',
      device: 'Chrome on MacOS',
      ip: '192.168.1.1',
      status: 'success',
    },
    {
      id: '2',
      type: 'suspicious_activity',
      description: 'Login attempt from new location',
      timestamp: '2025-06-15 22:15:00',
      location: 'London, UK',
      device: 'Safari on iOS',
      ip: '86.129.35.78',
      status: 'warning',
    },
    {
      id: '3',
      type: 'password_change',
      description: 'Password successfully changed',
      timestamp: '2025-06-10 09:45:00',
      location: 'New York, NY',
      device: 'Chrome on MacOS',
      ip: '192.168.1.1',
      status: 'success',
    },
    {
      id: '4',
      type: 'settings_change',
      description: 'Two-factor authentication enabled',
      timestamp: '2025-06-08 16:20:00',
      location: 'New York, NY',
      device: 'Mobile App',
      ip: '192.168.1.1',
      status: 'success',
    },
  ]);

  const [loginSessions] = useState<LoginSession[]>([
    {
      id: '1',
      device: 'Chrome on MacOS',
      browser: 'Chrome 126.0',
      location: 'New York, NY',
      ip: '192.168.1.1',
      lastActive: 'Active now',
      current: true,
    },
    {
      id: '2',
      device: 'Mobile App on iOS',
      browser: 'FinanceApp iOS',
      location: 'New York, NY',
      ip: '192.168.1.10',
      lastActive: '2 hours ago',
      current: false,
    },
    {
      id: '3',
      device: 'Safari on MacOS',
      browser: 'Safari 17.5',
      location: 'Brooklyn, NY',
      ip: '192.168.1.15',
      lastActive: 'Yesterday',
      current: false,
    },
  ]);

  useEffect(() => {
    // Enhanced page view logging
      text: `User ${user?.username || 'unknown'} viewed security page`,
      page_name: 'Security',
      user_id: user?.id,
      timestamp: new Date().toISOString(),
      data: {
        available_features: ['password_management', 'two_factor_auth', 'biometric_login', 'session_management'],
        security_score: securityScore,
        two_factor_enabled: twoFactorEnabled,
        biometric_enabled: biometricEnabled,
        active_sessions_count: loginSessions.length,
        recent_events_count: securityEvents.length
      }
    });

    // Simulate loading
    setTimeout(() => {
      setIsLoading(false);
    }, 500);
  }, [user]);

  const calculateSecurityScore = () => {
    let score = 40; // Base score
    if (twoFactorEnabled) score += 30;
    if (biometricEnabled) score += 20;
    if (securityEvents.filter(e => e.status === 'warning').length === 0) score += 10;
    return Math.min(score, 100);
  };

  useEffect(() => {
    setSecurityScore(calculateSecurityScore());
  }, [twoFactorEnabled, biometricEnabled]);

  const getSecurityScoreColor = () => {
    if (securityScore >= 80) return 'text-[var(--primary-emerald)]';
    if (securityScore >= 60) return 'text-[var(--primary-amber)]';
    return 'text-[var(--primary-red)]';
  };

  const getSecurityScoreLabel = () => {
    if (securityScore >= 80) return 'Excellent';
    if (securityScore >= 60) return 'Good';
    return 'Needs Improvement';
  };

  const getEventIcon = (type: SecurityEvent['type']) => {
    switch (type) {
      case 'login': return <Monitor className="w-4 h-4" />;
      case 'password_change': return <Key className="w-4 h-4" />;
      case 'settings_change': return <Settings className="w-4 h-4" />;
      case 'suspicious_activity': return <AlertTriangle className="w-4 h-4" />;
    }
  };

  const getEventColor = (status: SecurityEvent['status']) => {
    switch (status) {
      case 'success': return 'text-[var(--primary-emerald)]';
      case 'failed': return 'text-[var(--primary-red)]';
      case 'warning': return 'text-[var(--primary-amber)]';
    }
  };

  const handleSetupTwoFactor = async (method: 'authenticator' | 'sms' | 'email') => {
    try {
      setSetupStartTime(Date.now());
      const setupData: any = { method };
      
      if (method === 'sms' && phoneNumber) {
        setupData.phone_number = phoneNumber;
      } else if (method === 'email' && email) {
        setupData.email = email;
      }
      
      const response = await fetch('/api/security/2fa/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(setupData),
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedTwoFactorMethod(method);
        
        if (method === 'authenticator') {
          // Show QR code for authenticator
        } else {
          // Code has been sent via SMS/Email
          console.log(data.message);
        }
      }
    } catch (error) {
      console.error('Error setting up 2FA:', error);
    }
  };

  const handleEnableTwoFactor = async (code: string) => {
    try {
      if (!selectedTwoFactorMethod) return;
      
      // Call backend API to verify the 2FA code
      const response = await fetch(`/api/security/2fa/verify/${selectedTwoFactorMethod}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });
      
      if (response.ok) {
        setTwoFactorEnabled(true);
        setShowEnableTwoFactorModal(false);
        const method = selectedTwoFactorMethod;
        setSelectedTwoFactorMethod(null);
          text: `User ${user?.username || 'unknown'} successfully enabled 2FA using ${method}`,
          custom_action: '2fa_enabled',
          data: {
            user_id: user?.id,
            method: method,
            security_score_increase: 30,
            new_security_score: securityScore + 30,
            setup_duration_seconds: Math.floor((Date.now() - setupStartTime) / 1000)
          }
        });
      } else {
        // Handle invalid code
        console.error('Invalid 2FA code');
          text: 'User entered invalid 2FA verification code',
          custom_action: '2fa_verification_failed',
          data: {
            user_id: user?.id,
            method: selectedTwoFactorMethod,
            error: 'invalid_code'
          }
        });
      }
    } catch (error) {
      console.error('Error verifying 2FA:', error);
    }
  };

  const handleDisableTwoFactor = () => {
    setTwoFactorEnabled(false);
    setShowDisableTwoFactorModal(false);
      text: `User ${user?.username || 'unknown'} disabled two-factor authentication`,
      custom_action: '2fa_disabled',
      data: {
        user_id: user?.id,
        security_score_decrease: 30,
        new_security_score: Math.max(securityScore - 30, 0),
        previous_security_score: securityScore,
        risk_warning_shown: true
      }
    });
  };

  const handleEndSession = (sessionId: string) => {
    const session = loginSessions.find(s => s.id === sessionId);
      text: `User ${user?.username || 'unknown'} ended session on ${session?.device || 'unknown device'}`,
      custom_action: 'end_session',
      data: {
        user_id: user?.id,
        session_id: sessionId,
        session_device: session?.device,
        session_location: session?.location,
        session_browser: session?.browser,
        last_active: session?.lastActive,
        from_location: 'session_list'
      }
    });
    console.log('Ending session:', sessionId);
  };

  if (isLoading) {
    return (
      <div className="h-[calc(100vh-4rem)]">
        <div className="flex items-center justify-center h-96">
          <div className="text-[var(--text-2)]">Loading security settings...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-[var(--text-1)]">Security Center</h1>
            <p className="text-[var(--text-2)] mt-2">
              Protect your account and monitor security activity
            </p>
          </div>

          {/* Security Score */}
          <Card variant="default" className="mb-8">
            <CardBody>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                  <div className="relative">
                    <svg className="w-24 h-24 -rotate-90">
                      <circle
                        cx="48"
                        cy="48"
                        r="36"
                        stroke="var(--border-1)"
                        strokeWidth="8"
                        fill="none"
                      />
                      <motion.circle
                        cx="48"
                        cy="48"
                        r="36"
                        stroke="url(#security-gradient)"
                        strokeWidth="8"
                        fill="none"
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 36}`}
                        initial={{ strokeDashoffset: 2 * Math.PI * 36 }}
                        animate={{ strokeDashoffset: 2 * Math.PI * 36 * (1 - securityScore / 100) }}
                        transition={{ duration: 1, ease: 'easeInOut' }}
                      />
                      <defs>
                        <linearGradient id="security-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="var(--primary-blue)" />
                          <stop offset="100%" stopColor="var(--primary-emerald)" />
                        </linearGradient>
                      </defs>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <p className={`text-2xl font-bold ${getSecurityScoreColor()}`}>
                          {securityScore}
                        </p>
                        <p className="text-xs text-[var(--text-2)]">Score</p>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h2 className="text-xl font-semibold text-[var(--text-1)]">
                      Security Score: {getSecurityScoreLabel()}
                    </h2>
                    <p className="text-[var(--text-2)] mt-1">
                      {securityScore < 80 && 'Enable more security features to improve your score'}
                      {securityScore >= 80 && 'Your account is well protected'}
                    </p>
                  </div>
                </div>
                
                <Button 
                  variant="secondary" 
                  icon={<Download size={18} />}
                  onClick={async () => {
                      text: `User ${user?.username || 'unknown'} downloading security report`,
                      custom_action: 'download_security_report',
                      data: {
                        user_id: user?.id,
                        security_score: securityScore,
                        security_status: getSecurityScoreLabel(),
                        two_factor_enabled: twoFactorEnabled,
                        biometric_enabled: biometricEnabled,
                        active_sessions: loginSessions.length,
                        suspicious_events: securityEvents.filter(e => e.status === 'warning').length,
                        report_format: 'pdf'
                      }
                    });
                    
                    // Download security report PDF from backend
                    try {
                      const response = await securityApi.downloadSecurityReport();
                      const url = window.URL.createObjectURL(response);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `security_report_${new Date().toISOString().split('T')[0]}.pdf`;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      window.URL.revokeObjectURL(url);
                    } catch (error) {
                      console.error('Failed to download security report:', error);
                      notificationService.error('Failed to generate security report. Please try again.');
                    }
                  }}
                >
                  Security Report
                </Button>
              </div>
            </CardBody>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Authentication Methods */}
            <Card variant="default">
              <CardHeader>
                <h3 className="text-lg font-semibold text-[var(--text-1)]">
                  Authentication Methods
                </h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  {/* Password */}
                  <div className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-r from-[var(--primary-blue)] to-[var(--primary-indigo)]">
                          <Lock className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h4 className="font-medium text-[var(--text-1)]">Password</h4>
                          <p className="text-sm text-[var(--text-2)]">Last changed 3 months ago</p>
                        </div>
                      </div>
                      <CheckCircle className="w-5 h-5 text-[var(--primary-emerald)]" />
                    </div>
                    <Button 
                      variant="secondary" 
                      size="sm" 
                      fullWidth
                      onClick={() => {
                          text: `User ${user?.username || 'unknown'} clicked Change Password button`,
                          custom_action: 'initiate_password_change',
                          data: {
                            user_id: user?.id,
                            last_password_change: '3 months ago',
                            from_security_section: 'authentication_methods',
                            security_score_before: securityScore
                          }
                        });
                        setShowChangePasswordModal(true);
                      }}
                    >
                      Change Password
                    </Button>
                  </div>

                  {/* Two-Factor Authentication */}
                  <div className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-r from-[var(--primary-indigo)] to-[var(--primary-violet)]">
                          <Smartphone className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h4 className="font-medium text-[var(--text-1)]">Two-Factor Authentication</h4>
                          <p className="text-sm text-[var(--text-2)]">
                            {twoFactorEnabled ? 'Enabled' : 'Add an extra layer of security'}
                          </p>
                        </div>
                      </div>
                      {twoFactorEnabled ? (
                        <CheckCircle className="w-5 h-5 text-[var(--primary-emerald)]" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-[var(--primary-amber)]" />
                      )}
                    </div>
                    <Button
                      variant={twoFactorEnabled ? "secondary" : "primary"}
                      size="sm"
                      fullWidth
                      onClick={() => {
                        const action = twoFactorEnabled ? 'manage_2fa' : 'enable_2fa';
                          text: `User ${user?.username || 'unknown'} clicked ${twoFactorEnabled ? 'Manage' : 'Enable'} 2FA button`,
                          custom_action: action,
                          data: {
                            user_id: user?.id,
                            two_factor_status: twoFactorEnabled ? 'enabled' : 'disabled',
                            security_score_impact: twoFactorEnabled ? 0 : 30,
                            current_security_score: securityScore,
                            from_security_section: 'authentication_methods'
                          }
                        });
                        twoFactorEnabled ? setShowDisableTwoFactorModal(true) : setShowEnableTwoFactorModal(true);
                      }}
                    >
                      {twoFactorEnabled ? 'Manage 2FA' : 'Enable 2FA'}
                    </Button>
                  </div>

                  {/* Biometric Authentication */}
                  <div className="p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-r from-[var(--primary-violet)] to-[var(--primary-purple)]">
                          <Fingerprint className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h4 className="font-medium text-[var(--text-1)]">Biometric Login</h4>
                          <p className="text-sm text-[var(--text-2)]">
                            {biometricEnabled ? 'Face ID enabled' : 'Use fingerprint or face recognition'}
                          </p>
                        </div>
                      </div>
                      {biometricEnabled ? (
                        <CheckCircle className="w-5 h-5 text-[var(--primary-emerald)]" />
                      ) : (
                        <XCircle className="w-5 h-5 text-[var(--text-2)]" />
                      )}
                    </div>
                    <BiometricAuth
                      onSuccess={() => {
                        const newState = !biometricEnabled;
                        setBiometricEnabled(newState);
                          text: `User ${user?.username || 'unknown'} ${newState ? 'enabled' : 'disabled'} biometric login`,
                          toggle_type: 'biometric_auth',
                          toggle_state: newState,
                          data: {
                            user_id: user?.id,
                            biometric_type: 'Face ID',
                            security_score_impact: newState ? 20 : -20,
                            current_security_score: securityScore,
                            from_security_section: 'authentication_methods'
                          }
                        });
                      }}
                      onCancel={() => {
                          text: 'User cancelled biometric authentication setup',
                          custom_action: 'biometric_auth_cancelled',
                          data: {
                            user_id: user?.id,
                            current_state: biometricEnabled
                          }
                        });
                        console.log('Biometric auth cancelled');
                      }}
                      requireSlideConfirm={!biometricEnabled}
                      autoStart={false}
                    />
                  </div>
                </div>
              </CardBody>
            </Card>

            {/* Recent Security Events */}
            <Card variant="default">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-[var(--text-1)]">
                    Recent Activity
                  </h3>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => {
                        text: 'User viewing all security activity',
                        custom_action: 'view_all_security_activity',
                        data: {
                          user_id: user?.id,
                          recent_events_shown: 4,
                          total_events: securityEvents.length,
                          warning_events: securityEvents.filter(e => e.status === 'warning').length,
                          from_section: 'recent_activity'
                        }
                      });
                      console.log('Navigate to activity history');
                    }}
                  >
                    View All
                  </Button>
                </div>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  {securityEvents.slice(0, 4).map((event, index) => (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-start gap-3 p-3 rounded-lg hover:bg-[rgba(var(--glass-rgb),0.05)] transition-colors"
                    >
                      <div className={`p-1.5 rounded-lg ${
                        event.status === 'warning' 
                          ? 'bg-[var(--primary-amber)]/10' 
                          : 'bg-[rgba(var(--glass-rgb),0.1)]'
                      }`}>
                        <div className={getEventColor(event.status)}>
                          {getEventIcon(event.type)}
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[var(--text-1)]">
                          {event.description}
                        </p>
                        <div className="flex items-center gap-3 mt-1 text-xs text-[var(--text-2)]">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {event.timestamp}
                          </span>
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {event.location}
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardBody>
            </Card>
          </div>

          {/* Active Sessions */}
          <Card variant="default">
            <CardHeader>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-[var(--text-1)]">
                  Active Sessions
                </h3>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<LogOut size={16} />}
                  onClick={() => {
                      text: `User ${user?.username || 'unknown'} signing out all other sessions`,
                      custom_action: 'sign_out_all_sessions',
                      data: {
                        user_id: user?.id,
                        total_sessions: loginSessions.length,
                        other_sessions_count: loginSessions.filter(s => !s.current).length,
                        affected_sessions: loginSessions.filter(s => !s.current).map(s => ({
                          device: s.device,
                          location: s.location,
                          last_active: s.lastActive
                        }))
                      }
                    });
                    console.log('Sign out all other sessions');
                  }}
                >
                  Sign Out All Other Sessions
                </Button>
              </div>
            </CardHeader>
            <CardBody>
              <div className="space-y-3">
                {loginSessions.map((session, index) => (
                  <motion.div
                    key={session.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center justify-between p-4 rounded-lg border border-[var(--border-1)] hover:bg-[rgba(var(--glass-rgb),0.02)] transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-lg ${
                        session.current 
                          ? 'bg-gradient-to-r from-[var(--primary-emerald)] to-[var(--primary-teal)]' 
                          : 'bg-[rgba(var(--glass-rgb),0.1)]'
                      }`}>
                        <Monitor className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-[var(--text-1)]">{session.device}</h4>
                          {session.current && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--primary-emerald)]/10 text-[var(--primary-emerald)]">
                              Current
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-sm text-[var(--text-2)]">
                          <span className="flex items-center gap-1">
                            <Globe className="w-3 h-3" />
                            {session.location}
                          </span>
                          <span>•</span>
                          <span>{session.ip}</span>
                          <span>•</span>
                          <span>{session.lastActive}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedSession(session);
                          setShowSessionDetailsModal(true);
                            text: `User viewing details for session on ${session.device}`,
                            custom_action: 'view_session_details',
                            data: {
                              user_id: user?.id,
                              session_id: session.id,
                              session_device: session.device,
                              session_location: session.location,
                              session_browser: session.browser,
                              is_current_session: session.current,
                              last_active: session.lastActive
                            }
                          });
                        }}
                      >
                        Details
                      </Button>
                      {!session.current && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEndSession(session.id)}
                        >
                          End Session
                        </Button>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardBody>
          </Card>

          {/* Trusted Devices */}
          <Card variant="default" className="mt-8">
            <CardHeader>
              <h3 className="text-lg font-semibold text-[var(--text-1)]">
                Trusted Devices
              </h3>
              <p className="text-sm text-[var(--text-2)] mt-1">
                Devices that don't require two-factor authentication
              </p>
            </CardHeader>
            <CardBody>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 rounded-lg border border-[var(--border-1)]">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gradient-to-r from-[var(--primary-blue)] to-[var(--primary-indigo)]">
                      <Smartphone className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h4 className="font-medium text-[var(--text-1)]">iPhone 14 Pro</h4>
                      <p className="text-sm text-[var(--text-2)]">Added on Oct 15, 2025</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                        text: 'User removed trusted device',
                        custom_action: 'remove_trusted_device',
                        data: {
                          user_id: user?.id,
                          device_name: 'iPhone 14 Pro',
                          trusted_since: 'Oct 15, 2025'
                        }
                      });
                    }}
                  >
                    Remove
                  </Button>
                </div>
                
                <div className="flex items-center justify-between p-4 rounded-lg border border-[var(--border-1)]">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gradient-to-r from-[var(--primary-indigo)] to-[var(--primary-violet)]">
                      <Monitor className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h4 className="font-medium text-[var(--text-1)]">MacBook Pro</h4>
                      <p className="text-sm text-[var(--text-2)]">Added on Sep 20, 2025</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                        text: 'User removed trusted device',
                        custom_action: 'remove_trusted_device',
                        data: {
                          user_id: user?.id,
                          device_name: 'MacBook Pro',
                          trusted_since: 'Sep 20, 2025'
                        }
                      });
                    }}
                  >
                    Remove
                  </Button>
                </div>
                
                <div className="mt-4 p-4 rounded-lg bg-[rgba(var(--glass-rgb),0.05)] border border-[var(--border-1)]">
                  <p className="text-sm text-[var(--text-2)]">
                    <AlertCircle className="inline w-4 h-4 mr-1" />
                    Trusted devices won't need to enter a verification code when signing in. Only trust devices you own and use regularly.
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Privacy Settings */}
          <Card variant="default" className="mt-8">
            <CardHeader>
              <h3 className="text-lg font-semibold text-[var(--text-1)]">
                Privacy Settings
              </h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-[var(--text-1)]">Login Notifications</h4>
                    <p className="text-sm text-[var(--text-2)] mt-1">
                      Get notified when someone logs into your account
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer" 
                      defaultChecked 
                      onChange={(e) => {
                          text: `User ${e.target.checked ? 'enabled' : 'disabled'} login notifications`,
                          toggle_type: 'login_notifications',
                          toggle_state: e.target.checked,
                          data: { user_id: user?.id }
                        });
                      }}
                    />
                    <div className="w-11 h-6 bg-[var(--border-1)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--primary-blue)]"></div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-[var(--text-1)]">Transaction Alerts</h4>
                    <p className="text-sm text-[var(--text-2)] mt-1">
                      Receive alerts for transactions above $100
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer" 
                      defaultChecked 
                      onChange={(e) => {
                          text: `User ${e.target.checked ? 'enabled' : 'disabled'} transaction alerts`,
                          toggle_type: 'transaction_alerts',
                          toggle_state: e.target.checked,
                          data: { user_id: user?.id }
                        });
                      }}
                    />
                    <div className="w-11 h-6 bg-[var(--border-1)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--primary-blue)]"></div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-[var(--text-1)]">Data Sharing</h4>
                    <p className="text-sm text-[var(--text-2)] mt-1">
                      Share anonymized data to improve our services
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer"
                      onChange={(e) => {
                          text: `User ${e.target.checked ? 'enabled' : 'disabled'} data sharing`,
                          toggle_type: 'data_sharing',
                          toggle_state: e.target.checked,
                          data: { user_id: user?.id }
                        });
                      }}
                    />
                    <div className="w-11 h-6 bg-[var(--border-1)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--primary-blue)]"></div>
                  </label>
                </div>
                
                <div className="pt-4 flex gap-3">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                        text: 'User downloading personal data',
                        custom_action: 'download_personal_data',
                        data: { user_id: user?.id }
                      });
                      notificationService.info('Your data export will be ready in 24 hours', {
                        duration: 5000
                      });
                    }}
                  >
                    Download My Data
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => {
                        text: 'User initiated account deletion',
                        custom_action: 'delete_account_request',
                        data: { user_id: user?.id }
                      });
                      notificationService.warning('Account deletion requires additional verification', {
                        duration: 5000,
                        action: {
                          label: 'Contact Support',
                          onClick: () => console.log('Contact support')
                        }
                      });
                    }}
                  >
                    Delete Account
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Security Activity Log */}
          <Card variant="default" className="mt-8">
            <CardHeader>
              <h3 className="text-lg font-semibold text-[var(--text-1)]">
                Security Activity
              </h3>
              <p className="text-sm text-[var(--text-2)] mt-1">
                Recent security events on your account
              </p>
            </CardHeader>
            <CardBody>
              <div className="space-y-3">
                {securityEvents.slice(0, 5).map((event, index) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-start gap-3 p-3 rounded-lg bg-[rgba(var(--glass-rgb),0.02)] border border-[var(--border-1)]"
                  >
                    <div className={`p-2 rounded-lg ${
                      event.status === 'success' 
                        ? 'bg-[var(--primary-emerald)]/10' 
                        : event.status === 'warning' 
                        ? 'bg-[var(--primary-amber)]/10'
                        : 'bg-[var(--primary-red)]/10'
                    }`}>
                      {event.type === 'login' && <LogOut className={`w-4 h-4 ${
                        event.status === 'success' ? 'text-[var(--primary-emerald)]' : 
                        event.status === 'warning' ? 'text-[var(--primary-amber)]' : 
                        'text-[var(--primary-red)]'
                      }`} />}
                      {event.type === 'password_change' && <Key className="w-4 h-4 text-[var(--primary-blue)]" />}
                      {event.type === 'settings_change' && <Settings className="w-4 h-4 text-[var(--primary-indigo)]" />}
                      {event.type === 'suspicious_activity' && <AlertTriangle className="w-4 h-4 text-[var(--primary-amber)]" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-medium text-[var(--text-1)]">{event.description}</h4>
                        <span className="text-xs text-[var(--text-2)]">{event.timestamp}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-[var(--text-2)]">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {event.location}
                        </span>
                        <span>•</span>
                        <span>{event.device}</span>
                      </div>
                    </div>
                  </motion.div>
                ))}
                
                <Button
                  variant="secondary"
                  size="sm"
                  fullWidth
                  onClick={() => {
                      text: 'User viewing full security activity log',
                      custom_action: 'view_full_security_log',
                      data: {
                        user_id: user?.id,
                        total_events: securityEvents.length,
                        suspicious_events: securityEvents.filter(e => e.status === 'warning').length
                      }
                    });
                  }}
                >
                  View All Activity
                </Button>
              </div>
            </CardBody>
          </Card>

          {/* Security Recommendations */}
          <Card variant="subtle" className="mt-8">
            <CardHeader>
              <h3 className="text-lg font-semibold text-[var(--text-1)]">
                Security Recommendations
              </h3>
            </CardHeader>
            <CardBody>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {!twoFactorEnabled && (
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-[var(--primary-amber)]/10 border border-[var(--primary-amber)]/20">
                    <AlertTriangle className="w-5 h-5 text-[var(--primary-amber)] mt-0.5" />
                    <div className="flex-1">
                      <h4 className="font-medium text-[var(--text-1)]">Enable Two-Factor Authentication</h4>
                      <p className="text-sm text-[var(--text-2)] mt-1">
                        Add an extra layer of security to your account
                      </p>
                      <Button
                        variant="secondary"
                        size="sm"
                        className="mt-2"
                        onClick={() => {
                            text: 'User clicked Enable Now for 2FA from security recommendations',
                            custom_action: 'enable_2fa_from_recommendations',
                            data: {
                              user_id: user?.id,
                              from_section: 'security_recommendations',
                              current_security_score: securityScore,
                              potential_score_increase: 30
                            }
                          });
                          setShowEnableTwoFactorModal(true);
                        }}
                      >
                        Enable Now
                      </Button>
                    </div>
                  </div>
                )}
                
                {!biometricEnabled && (
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-[var(--primary-blue)]/10 border border-[var(--primary-blue)]/20">
                    <Fingerprint className="w-5 h-5 text-[var(--primary-blue)] mt-0.5" />
                    <div className="flex-1">
                      <h4 className="font-medium text-[var(--text-1)]">Set Up Biometric Login</h4>
                      <p className="text-sm text-[var(--text-2)] mt-1">
                        Use your fingerprint or face for quick access
                      </p>
                      <Button
                        variant="secondary"
                        size="sm"
                        className="mt-2"
                      >
                        Set Up
                      </Button>
                    </div>
                  </div>
                )}
                
                <div className="flex items-start gap-3 p-4 rounded-lg bg-[var(--primary-emerald)]/10 border border-[var(--primary-emerald)]/20">
                  <ShieldCheck className="w-5 h-5 text-[var(--primary-emerald)] mt-0.5" />
                  <div className="flex-1">
                    <h4 className="font-medium text-[var(--text-1)]">Regular Security Checkup</h4>
                    <p className="text-sm text-[var(--text-2)] mt-1">
                      Review your security settings monthly
                    </p>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      {/* Enable Two-Factor Modal */}
      <Modal
        isOpen={showEnableTwoFactorModal}
        onClose={() => {
          setShowEnableTwoFactorModal(false);
          setSelectedTwoFactorMethod(null);
        }}
        title="Enable Two-Factor Authentication"
        size="md"
      >
        <div className="space-y-4">
          {!selectedTwoFactorMethod ? (
            <>
              <p className="text-[var(--text-2)]">
                Choose your preferred two-factor authentication method:
              </p>
              
              <div className="space-y-3">
                {/* Authenticator App */}
                <button
                  onClick={() => {
                      text: 'User selected authenticator app for 2FA setup',
                      custom_action: 'select_2fa_method',
                      data: {
                        user_id: user?.id,
                        method: 'authenticator',
                        is_recommended: true
                      }
                    });
                    handleSetupTwoFactor('authenticator');
                  }}
                  className="w-full p-4 text-left rounded-lg border border-[var(--border-1)] hover:bg-[rgba(var(--glass-rgb),0.05)] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gradient-to-r from-[var(--primary-blue)] to-[var(--primary-indigo)]">
                      <Smartphone className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-[var(--text-1)]">Authenticator App</h4>
                      <p className="text-sm text-[var(--text-2)]">Use Google Authenticator, Authy, or similar</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-[var(--text-2)]" />
                  </div>
                </button>
                
                {/* SMS */}
                <button
                  onClick={() => {
                      text: 'User selected SMS for 2FA setup',
                      custom_action: 'select_2fa_method',
                      data: {
                        user_id: user?.id,
                        method: 'sms',
                        is_recommended: false
                      }
                    });
                    setSelectedTwoFactorMethod('sms');
                  }}
                  className="w-full p-4 text-left rounded-lg border border-[var(--border-1)] hover:bg-[rgba(var(--glass-rgb),0.05)] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gradient-to-r from-[var(--primary-indigo)] to-[var(--primary-violet)]">
                      <Smartphone className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-[var(--text-1)]">SMS Text Message</h4>
                      <p className="text-sm text-[var(--text-2)]">Receive codes via text message</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-[var(--text-2)]" />
                  </div>
                </button>
                
                {/* Email */}
                <button
                  onClick={() => {
                      text: 'User selected email for 2FA setup',
                      custom_action: 'select_2fa_method',
                      data: {
                        user_id: user?.id,
                        method: 'email',
                        is_recommended: false
                      }
                    });
                    setSelectedTwoFactorMethod('email');
                  }}
                  className="w-full p-4 text-left rounded-lg border border-[var(--border-1)] hover:bg-[rgba(var(--glass-rgb),0.05)] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gradient-to-r from-[var(--primary-violet)] to-[var(--primary-purple)]">
                      <Key className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-[var(--text-1)]">Email</h4>
                      <p className="text-sm text-[var(--text-2)]">Receive codes via email</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-[var(--text-2)]" />
                  </div>
                </button>
              </div>
            </>
          ) : selectedTwoFactorMethod === 'sms' ? (
            <>
              <p className="text-[var(--text-2)]">
                Enter your phone number to receive verification codes:
              </p>
              <Input
                type="tel"
                placeholder="+1234567890"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
              />
              <Button
                variant="primary"
                fullWidth
                onClick={() => handleSetupTwoFactor('sms')}
                disabled={!phoneNumber}
              >
                Send Verification Code
              </Button>
              {phoneNumber && (
                <TwoFactorInput
                  onComplete={handleEnableTwoFactor}
                  onResend={() => handleSetupTwoFactor('sms')}
                />
              )}
            </>
          ) : selectedTwoFactorMethod === 'email' ? (
            <>
              <p className="text-[var(--text-2)]">
                Enter your email address to receive verification codes:
              </p>
              <Input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Button
                variant="primary"
                fullWidth
                onClick={() => handleSetupTwoFactor('email')}
                disabled={!email}
              >
                Send Verification Code
              </Button>
              {email && (
                <TwoFactorInput
                  onComplete={handleEnableTwoFactor}
                  onResend={() => handleSetupTwoFactor('email')}
                />
              )}
            </>
          ) : (
            <>
              <p className="text-[var(--text-2)]">
                Scan this QR code with your authenticator app, then enter the verification code below.
              </p>
              
              <div className="p-4 glass-card rounded-lg mx-auto w-48 h-48">
                {/* QR Code placeholder */}
                <div className="w-full h-full bg-surface-alt rounded flex items-center justify-center">
                  <span className="text-secondary">QR Code</span>
                </div>
              </div>
              
              <div className="text-center">
                <p className="text-sm text-[var(--text-2)] mb-2">Or enter this key manually:</p>
                <code className="text-xs bg-[rgba(var(--glass-rgb),0.1)] px-2 py-1 rounded">
                  ABCD-EFGH-IJKL-MNOP
                </code>
              </div>
              
              <TwoFactorInput
                onComplete={handleEnableTwoFactor}
                onResend={() => console.log('Resend code')}
              />
            </>
          )}
        </div>
      </Modal>

      {/* Disable Two-Factor Modal */}
      <Modal
        isOpen={showDisableTwoFactorModal}
        onClose={() => setShowDisableTwoFactorModal(false)}
        title="Disable Two-Factor Authentication"
        size="md"
      >
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-[var(--primary-amber)]/10 border border-[var(--primary-amber)]/20">
            <p className="text-sm text-[var(--primary-amber)]">
              Warning: Disabling 2FA will make your account less secure.
            </p>
          </div>
          
          <p className="text-[var(--text-2)]">
            Are you sure you want to disable two-factor authentication?
          </p>
          
          <SlideToConfirm
            text="Slide to disable 2FA"
            onConfirm={handleDisableTwoFactor}
          />
        </div>
      </Modal>

      {/* Session Details Modal */}
      <Modal
        isOpen={showSessionDetailsModal}
        onClose={() => {
          setShowSessionDetailsModal(false);
          setSelectedSession(null);
        }}
        title="Session Details"
        size="md"
      >
        {selectedSession && (
          <div className="space-y-4">
            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b border-[var(--border-1)]">
                <span className="text-sm text-[var(--text-2)]">Device</span>
                <span className="text-sm font-medium text-[var(--text-1)]">{selectedSession.device}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-[var(--border-1)]">
                <span className="text-sm text-[var(--text-2)]">Browser</span>
                <span className="text-sm font-medium text-[var(--text-1)]">{selectedSession.browser}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-[var(--border-1)]">
                <span className="text-sm text-[var(--text-2)]">Location</span>
                <span className="text-sm font-medium text-[var(--text-1)]">{selectedSession.location}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-[var(--border-1)]">
                <span className="text-sm text-[var(--text-2)]">IP Address</span>
                <span className="text-sm font-medium text-[var(--text-1)]">{selectedSession.ip}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-[var(--border-1)]">
                <span className="text-sm text-[var(--text-2)]">Last Active</span>
                <span className="text-sm font-medium text-[var(--text-1)]">{selectedSession.lastActive}</span>
              </div>
            </div>
            
            {!selectedSession.current && (
              <Button
                variant="danger"
                fullWidth
                onClick={() => {
                  handleEndSession(selectedSession.id);
                  setShowSessionDetailsModal(false);
                }}
              >
                End This Session
              </Button>
            )}
          </div>
        )}
      </Modal>

      {/* Change Password Modal */}
      <Modal
        isOpen={showChangePasswordModal}
        onClose={() => {
          setShowChangePasswordModal(false);
          setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
        }}
        title="Change Password"
        size="md"
      >
        <form 
          className="space-y-4"
          onSubmit={async (e) => {
            e.preventDefault();
            if (passwordForm.newPassword !== passwordForm.confirmPassword) {
              notificationService.error('Passwords do not match');
              return;
            }
            
            const passwordStrength = checkPasswordStrength(passwordForm.newPassword);
            if (!passwordStrength.isStrong) {
              notificationService.warning('Please choose a stronger password', {
                duration: 6000
              });
              if (passwordStrength.feedback.length > 0) {
                passwordStrength.feedback.forEach(tip => {
                  notificationService.info(tip, { duration: 6000 });
                });
              }
              return;
            }
            
            try {
              await notificationService.promise(
                securityApi.changePassword({
                  currentPassword: passwordForm.currentPassword,
                  newPassword: passwordForm.newPassword
                }),
                {
                  loading: 'Changing password...',
                  success: 'Password changed successfully!',
                  error: (err) => {
                    if (err.message?.includes('401') || err.message?.includes('Incorrect')) {
                      return 'Current password is incorrect';
                    }
                    return 'Failed to change password. Please try again.';
                  }
                }
              );
              
                text: 'User successfully changed password',
                custom_action: 'password_changed',
                data: {
                  user_id: user?.id,
                  password_strength_score: passwordStrength.score,
                  password_strength_label: passwordStrength.score <= 2 ? 'weak' : passwordStrength.score <= 3 ? 'medium' : 'strong',
                  from_security_page: true
                }
              });
              
              setShowChangePasswordModal(false);
              setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
            } catch (error) {
              console.error('Password change error:', error);
            }
          }}
        >
          <div>
            <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
              Current Password
            </label>
            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                value={passwordForm.currentPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                required
                placeholder="Enter current password"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-2)] hover:text-[var(--text-1)]"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
              New Password
            </label>
            <Input
              type="password"
              value={passwordForm.newPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
              required
              placeholder="Enter new password"
              minLength={8}
            />
            
            {/* Password Strength Indicator */}
            {passwordForm.newPassword && (
              <div className="mt-2">
                <div className="flex items-center gap-2 mb-1">
                  <div className="flex-1 h-2 bg-[rgba(var(--glass-rgb),0.1)] rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full ${
                        checkPasswordStrength(passwordForm.newPassword).score <= 2 
                          ? 'bg-[var(--primary-red)]' 
                          : checkPasswordStrength(passwordForm.newPassword).score <= 3 
                          ? 'bg-[var(--primary-amber)]' 
                          : 'bg-[var(--primary-emerald)]'
                      }`}
                      initial={{ width: 0 }}
                      animate={{ width: `${(checkPasswordStrength(passwordForm.newPassword).score / 5) * 100}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <span className={`text-xs font-medium ${
                    checkPasswordStrength(passwordForm.newPassword).score <= 2 
                      ? 'text-[var(--primary-red)]' 
                      : checkPasswordStrength(passwordForm.newPassword).score <= 3 
                      ? 'text-[var(--primary-amber)]' 
                      : 'text-[var(--primary-emerald)]'
                  }`}>
                    {checkPasswordStrength(passwordForm.newPassword).score <= 2 ? 'Weak' : 
                     checkPasswordStrength(passwordForm.newPassword).score <= 3 ? 'Medium' : 'Strong'}
                  </span>
                </div>
                {checkPasswordStrength(passwordForm.newPassword).feedback.length > 0 && (
                  <ul className="text-xs text-[var(--text-2)] space-y-1">
                    {checkPasswordStrength(passwordForm.newPassword).feedback.map((tip, index) => (
                      <li key={index} className="flex items-start gap-1">
                        <span className="text-[var(--primary-amber)]">•</span>
                        {tip}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-[var(--text-1)] mb-2">
              Confirm New Password
            </label>
            <Input
              type="password"
              value={passwordForm.confirmPassword}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
              required
              placeholder="Confirm new password"
            />
          </div>
          
          <div className="flex gap-3 justify-end pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setShowChangePasswordModal(false);
                setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword}
            >
              Change Password
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
