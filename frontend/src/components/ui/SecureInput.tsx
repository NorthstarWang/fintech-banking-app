'use client';

import React, { useState, useCallback, forwardRef } from 'react';
import { InputSanitizer } from '@/utils/InputSanitizer';
import { motion } from 'framer-motion';

interface SecureInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  sanitizeType?: 'text' | 'email' | 'phone' | 'currency' | 'number' | 'url';
  onChange?: (value: string, sanitized: string) => void;
  onSanitizationError?: (error: string) => void;
  showSanitizationFeedback?: boolean;
  maskWhenBlurred?: boolean;
  maskType?: 'account' | 'card' | 'ssn' | 'phone';
}

const SecureInput = forwardRef<HTMLInputElement, SecureInputProps>(
  (
    {
      sanitizeType = 'text',
      onChange,
      onSanitizationError,
      showSanitizationFeedback = true,
      maskWhenBlurred = false,
      maskType,
      value: propValue,
      type = 'text',
      className = '',
      ...props
    },
    ref
  ) => {
    const [value, setValue] = useState(propValue?.toString() || '');
    const [sanitizedValue, setSanitizedValue] = useState('');
    const [isFocused, setIsFocused] = useState(false);
    const [sanitizationError, setSanitizationError] = useState<string | null>(null);
    const [showPassword, setShowPassword] = useState(false);

    const sanitize = useCallback((input: string): string => {
      let sanitized = '';
      let error: string | null = null;

      try {
        switch (sanitizeType) {
          case 'email':
            sanitized = InputSanitizer.sanitizeEmail(input);
            if (!sanitized && input) {
              error = 'Invalid email format';
            }
            break;
          case 'phone':
            sanitized = InputSanitizer.sanitizePhone(input);
            if (!sanitized && input) {
              error = 'Invalid phone number';
            }
            break;
          case 'currency':
            const amount = InputSanitizer.sanitizeCurrency(input);
            sanitized = amount.toString();
            break;
          case 'number':
            const num = InputSanitizer.sanitizeNumber(input);
            sanitized = num !== null ? num.toString() : '';
            if (!sanitized && input) {
              error = 'Invalid number';
            }
            break;
          case 'url':
            sanitized = InputSanitizer.sanitizeURL(input);
            if (!sanitized && input) {
              error = 'Invalid URL';
            }
            break;
          default:
            sanitized = InputSanitizer.sanitizeText(input);
            break;
        }
      } catch (e) {
        error = 'Sanitization error';
        sanitized = '';
      }

      setSanitizationError(error);
      if (error && onSanitizationError) {
        onSanitizationError(error);
      }

      return sanitized;
    }, [sanitizeType, onSanitizationError]);

    const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
      const rawValue = e.target.value;
      const sanitized = sanitize(rawValue);
      
      setValue(rawValue);
      setSanitizedValue(sanitized);
      
      if (onChange) {
        onChange(rawValue, sanitized);
      }
    }, [sanitize, onChange]);

    const handleFocus = useCallback(() => {
      setIsFocused(true);
    }, []);

    const handleBlur = useCallback(() => {
      setIsFocused(false);
      
      // Apply sanitized value on blur
      if (sanitizedValue !== value) {
        setValue(sanitizedValue);
      }
    }, [sanitizedValue, value]);

    const displayValue = () => {
      if (maskWhenBlurred && !isFocused && maskType && value) {
        return InputSanitizer.maskData(value, maskType);
      }
      return value;
    };

    const inputType = type === 'password' && showPassword ? 'text' : type;

    return (
      <div className="relative">
        <div className="relative">
          <input
            ref={ref}
            type={inputType}
            value={displayValue()}
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            className={`
              ${className}
              ${sanitizationError ? 'border-red-500 focus:ring-red-500' : ''}
              ${maskWhenBlurred && !isFocused ? 'font-mono' : ''}
            `}
            {...props}
          />
          
          {type === 'password' && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            >
              {showPassword ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              )}
            </button>
          )}
        </div>

        {showSanitizationFeedback && sanitizationError && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-red-500 text-sm mt-1"
          >
            {sanitizationError}
          </motion.p>
        )}

        {showSanitizationFeedback && !sanitizationError && value !== sanitizedValue && value && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-yellow-600 text-sm mt-1"
          >
            Input will be sanitized on blur
          </motion.p>
        )}
      </div>
    );
  }
);

SecureInput.displayName = 'SecureInput';

export default SecureInput;