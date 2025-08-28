import {
  generateSecureToken,
  checkPasswordStrength,
  apiRateLimiter,
  authRateLimiter,
  transferRateLimiter,
  generateCSRFToken,
  validateCSRFToken,
} from '../security'

describe('Security Utilities', () => {
  describe('generateSecureToken', () => {
    it('should generate a token of default length', () => {
      const token = generateSecureToken()
      expect(token).toHaveLength(64) // 32 bytes = 64 hex characters
    })

    it('should generate a token of specified length', () => {
      const token = generateSecureToken(16)
      expect(token).toHaveLength(32) // 16 bytes = 32 hex characters
    })

    it('should generate different tokens each time', () => {
      const token1 = generateSecureToken()
      const token2 = generateSecureToken()
      expect(token1).not.toBe(token2)
    })

    it('should only contain valid hex characters', () => {
      const token = generateSecureToken()
      expect(token).toMatch(/^[0-9a-f]+$/)
    })
  })

  describe('checkPasswordStrength', () => {
    it('should return weak score for short passwords', () => {
      const result = checkPasswordStrength('abc123')
      expect(result.score).toBeLessThan(4)
      expect(result.isStrong).toBe(false)
      expect(result.feedback).toContain('Password must be at least 8 characters long')
    })

    it('should return strong score for complex passwords', () => {
      const result = checkPasswordStrength('MyStr0ng!P@ssw0rd')
      expect(result.score).toBeGreaterThanOrEqual(4)
      expect(result.isStrong).toBe(true)
      expect(result.feedback).toHaveLength(0)
    })

    it('should provide feedback for missing character types', () => {
      const result = checkPasswordStrength('onlylowercase')
      expect(result.feedback).toContain('Include uppercase letters')
      expect(result.feedback).toContain('Include numbers')
      expect(result.feedback).toContain('Include special characters')
    })

    it('should penalize common patterns', () => {
      const result1 = checkPasswordStrength('Password123!')
      const result2 = checkPasswordStrength('Str0ng!Sec#')
      expect(result1.score).toBeLessThanOrEqual(result2.score)
      expect(result1.feedback).toContain('Avoid common patterns')
    })

    it('should penalize repeated characters', () => {
      const result = checkPasswordStrength('Passsword123!')
      expect(result.feedback).toContain('Avoid repeated characters')
    })

    it('should provide length recommendation for 8-11 character passwords', () => {
      const result = checkPasswordStrength('Pass123!')
      expect(result.feedback).toContain('Use at least 12 characters for a stronger password')
    })
  })

  describe('Rate Limiters', () => {
    beforeEach(() => {
      // Clean up rate limiters before each test
      apiRateLimiter.cleanup()
      authRateLimiter.cleanup()
      transferRateLimiter.cleanup()
    })

    describe('apiRateLimiter', () => {
      it('should allow requests within limit', () => {
        const key = 'test-user-1'
        for (let i = 0; i < 10; i++) {
          expect(apiRateLimiter.isAllowed(key)).toBe(true)
        }
      })

      it('should block requests exceeding limit', () => {
        const key = 'test-user-2'
        // API rate limiter allows 100 requests per minute
        for (let i = 0; i < 100; i++) {
          apiRateLimiter.isAllowed(key)
        }
        expect(apiRateLimiter.isAllowed(key)).toBe(false)
      })

      it('should track remaining requests correctly', () => {
        const key = 'test-user-3'
        expect(apiRateLimiter.getRemainingRequests(key)).toBe(100)
        
        apiRateLimiter.isAllowed(key)
        expect(apiRateLimiter.getRemainingRequests(key)).toBe(99)
        
        apiRateLimiter.isAllowed(key)
        expect(apiRateLimiter.getRemainingRequests(key)).toBe(98)
      })

      it('should reset after time window', () => {
        const key = 'test-user-4'
        const originalDate = Date.now
        
        // Use up all requests
        for (let i = 0; i < 100; i++) {
          apiRateLimiter.isAllowed(key)
        }
        expect(apiRateLimiter.isAllowed(key)).toBe(false)
        
        // Mock time passing (61 seconds)
        Date.now = jest.fn(() => originalDate() + 61000)
        
        expect(apiRateLimiter.isAllowed(key)).toBe(true)
        
        // Restore Date.now
        Date.now = originalDate
      })
    })

    describe('authRateLimiter', () => {
      it('should limit auth attempts to 5 per 5 minutes', () => {
        const key = 'auth-test-user'
        for (let i = 0; i < 5; i++) {
          expect(authRateLimiter.isAllowed(key)).toBe(true)
        }
        expect(authRateLimiter.isAllowed(key)).toBe(false)
      })
    })

    describe('transferRateLimiter', () => {
      it('should limit transfers to 10 per hour', () => {
        const key = 'transfer-test-user'
        for (let i = 0; i < 10; i++) {
          expect(transferRateLimiter.isAllowed(key)).toBe(true)
        }
        expect(transferRateLimiter.isAllowed(key)).toBe(false)
      })
    })
  })

  describe('CSRF Token', () => {
    it('should generate CSRF tokens', () => {
      const token = generateCSRFToken()
      expect(token).toBeTruthy()
      expect(typeof token).toBe('string')
    })

    it('should generate different tokens each time', () => {
      const token1 = generateCSRFToken()
      const token2 = generateCSRFToken()
      expect(token1).not.toBe(token2)
    })

    it('should validate matching tokens', () => {
      const token = 'test-csrf-token'
      expect(validateCSRFToken(token, token)).toBe(true)
    })

    it('should reject mismatched tokens', () => {
      expect(validateCSRFToken('token1', 'token2')).toBe(false)
    })

    it('should reject empty tokens', () => {
      expect(validateCSRFToken('', '')).toBe(false)
    })
  })
})