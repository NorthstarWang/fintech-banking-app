/**
 * Browser-compatible security utilities
 */

// Generate secure random tokens
export async function generateSecureToken(length: number = 32): Promise<string> {
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// Hash sensitive data using Web Crypto API
export async function hashData(data: string): Promise<string> {
  const encoder = new TextEncoder();
  const dataBuffer = encoder.encode(data);
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
}

// Generate CSRF tokens
export function generateCSRFToken(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode.apply(null, Array.from(array)));
}

// Validate CSRF tokens
export function validateCSRFToken(token: string, sessionToken: string): boolean {
  return token === sessionToken && token.length > 0;
}

// Client-side rate limiting helper
interface RateLimitEntry {
  count: number;
  resetTime: number;
}

export class ClientRateLimiter {
  private limits: Map<string, RateLimitEntry> = new Map();
  
  constructor(
    private windowMs: number = 60000, // 1 minute
    private maxRequests: number = 10
  ) {}
  
  isAllowed(key: string): boolean {
    const now = Date.now();
    const entry = this.limits.get(key);
    
    if (!entry || entry.resetTime < now) {
      this.limits.set(key, { count: 1, resetTime: now + this.windowMs });
      return true;
    }
    
    if (entry.count >= this.maxRequests) {
      return false;
    }
    
    entry.count++;
    return true;
  }
  
  getRemainingRequests(key: string): number {
    const entry = this.limits.get(key);
    if (!entry || entry.resetTime < Date.now()) {
      return this.maxRequests;
    }
    return Math.max(0, this.maxRequests - entry.count);
  }
  
  getResetTime(key: string): number {
    const entry = this.limits.get(key);
    return entry?.resetTime || Date.now() + this.windowMs;
  }
  
  cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.limits.entries()) {
      if (entry.resetTime < now) {
        this.limits.delete(key);
      }
    }
  }
}

// Export rate limiter instances
export const apiRateLimiter = new ClientRateLimiter(60000, 100); // 100 requests per minute
export const authRateLimiter = new ClientRateLimiter(300000, 5); // 5 attempts per 5 minutes

// Password strength checker
export function checkPasswordStrength(password: string): {
  score: number;
  feedback: string[];
  isStrong: boolean;
} {
  const feedback: string[] = [];
  let score = 0;
  
  // Length check
  if (password.length >= 12) {
    score += 2;
  } else if (password.length >= 8) {
    score += 1;
    feedback.push('Use at least 12 characters for a stronger password');
  } else {
    feedback.push('Password must be at least 8 characters long');
  }
  
  // Complexity checks
  if (/[a-z]/.test(password)) score += 1;
  else feedback.push('Include lowercase letters');
  
  if (/[A-Z]/.test(password)) score += 1;
  else feedback.push('Include uppercase letters');
  
  if (/[0-9]/.test(password)) score += 1;
  else feedback.push('Include numbers');
  
  if (/[^a-zA-Z0-9]/.test(password)) score += 1;
  else feedback.push('Include special characters');
  
  // Common patterns check
  const commonPatterns = [
    /123/, /abc/, /password/i, /qwerty/i, /admin/i,
    /111/, /000/, /aaa/i, /letmein/i, /welcome/i
  ];
  
  const hasCommonPattern = commonPatterns.some(pattern => pattern.test(password));
  if (hasCommonPattern) {
    score -= 1;
    feedback.push('Avoid common patterns');
  }
  
  // Repeated characters check
  if (/(.)\1{2,}/.test(password)) {
    score -= 1;
    feedback.push('Avoid repeated characters');
  }
  
  // Dictionary words check (simplified)
  const commonWords = ['password', 'admin', 'user', 'login', 'welcome'];
  const lowerPassword = password.toLowerCase();
  if (commonWords.some(word => lowerPassword.includes(word))) {
    score -= 1;
    feedback.push('Avoid dictionary words');
  }
  
  return {
    score: Math.max(0, Math.min(5, score)),
    feedback,
    isStrong: score >= 4
  };
}

// Generate session fingerprint
export async function generateSessionFingerprint(): Promise<string> {
  const components = [
    navigator.userAgent || '',
    navigator.language || '',
    screen.width + 'x' + screen.height,
    screen.colorDepth.toString(),
    new Date().getTimezoneOffset().toString(),
    navigator.hardwareConcurrency?.toString() || '',
    // Canvas fingerprinting (simplified)
    await getCanvasFingerprint()
  ];
  
  const fingerprint = components.join('|');
  return hashData(fingerprint);
}

// Canvas fingerprinting helper
async function getCanvasFingerprint(): Promise<string> {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';
    
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('Canvas fingerprint', 2, 15);
    
    return canvas.toDataURL();
  } catch {
    return '';
  }
}

// Secure storage wrapper
export class SecureStorage {
  private storageKey = 'secure_';

  async setItem(key: string, value: unknown): Promise<void> {
    const stringValue = JSON.stringify(value);
    const hash = await hashData(stringValue);
    const data = {
      value: stringValue,
      hash,
      timestamp: Date.now()
    };
    localStorage.setItem(this.storageKey + key, JSON.stringify(data));
  }

  async getItem<T = unknown>(key: string): Promise<T | null> {
    const stored = localStorage.getItem(this.storageKey + key);
    if (!stored) return null;

    try {
      const data = JSON.parse(stored);
      const currentHash = await hashData(data.value);

      // Verify integrity
      if (currentHash !== data.hash) {
        this.removeItem(key);
        return null;
      }

      return JSON.parse(data.value) as T;
    } catch {
      return null;
    }
  }
  
  removeItem(key: string): void {
    localStorage.removeItem(this.storageKey + key);
  }
  
  clear(): void {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(this.storageKey)) {
        localStorage.removeItem(key);
      }
    });
  }
}

export const secureStorage = new SecureStorage();

// XSS protection helper
export function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// URL validation
export function isValidUrl(string: string): boolean {
  try {
    const url = new URL(string);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

// Email validation
export function isValidEmail(email: string): boolean {
  const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return re.test(email);
}

// Phone validation
export function isValidPhone(phone: string): boolean {
  const cleaned = phone.replace(/\D/g, '');
  return cleaned.length >= 10 && cleaned.length <= 15;
}

// Credit card validation (Luhn algorithm)
export function isValidCreditCard(cardNumber: string): boolean {
  const cleaned = cardNumber.replace(/\D/g, '');
  if (cleaned.length < 13 || cleaned.length > 19) return false;
  
  let sum = 0;
  let isEven = false;
  
  for (let i = cleaned.length - 1; i >= 0; i--) {
    let digit = parseInt(cleaned[i], 10);
    
    if (isEven) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }
    
    sum += digit;
    isEven = !isEven;
  }
  
  return sum % 10 === 0;
}

// Get credit card type
export function getCreditCardType(cardNumber: string): string {
  const cleaned = cardNumber.replace(/\D/g, '');
  
  const patterns = {
    visa: /^4[0-9]{12}(?:[0-9]{3})?$/,
    mastercard: /^5[1-5][0-9]{14}$/,
    amex: /^3[47][0-9]{13}$/,
    discover: /^6(?:011|5[0-9]{2})[0-9]{12}$/,
    diners: /^3(?:0[0-5]|[68][0-9])[0-9]{11}$/,
    jcb: /^(?:2131|1800|35\d{3})\d{11}$/
  };
  
  for (const [type, pattern] of Object.entries(patterns)) {
    if (pattern.test(cleaned)) {
      return type;
    }
  }
  
  return 'unknown';
}

// Format credit card number
export function formatCreditCard(cardNumber: string): string {
  const cleaned = cardNumber.replace(/\D/g, '');
  const parts = cleaned.match(/.{1,4}/g) || [];
  return parts.join(' ');
}

// Security headers for fetch requests
export function getSecureFetchHeaders(): HeadersInit {
  return {
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRF-Token': generateCSRFToken(),
  };
}

// Detect suspicious activity patterns
export function detectSuspiciousActivity(activities: Array<{ timestamp: number; type: string }>): boolean {
  const recentActivities = activities.filter(a => 
    Date.now() - a.timestamp < 60000 // Last minute
  );
  
  // Too many activities in short time
  if (recentActivities.length > 20) return true;
  
  // Repeated failed attempts
  const failedAttempts = recentActivities.filter(a => 
    a.type.includes('failed') || a.type.includes('error')
  );
  if (failedAttempts.length > 5) return true;
  
  // Rapid consecutive actions
  for (let i = 1; i < recentActivities.length; i++) {
    if (recentActivities[i].timestamp - recentActivities[i-1].timestamp < 100) {
      return true; // Less than 100ms between actions
    }
  }
  
  return false;
}