import { apiClient } from './client';

interface LoginCredentials {
  username: string;
  password: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    role: string;
  };
}

interface UserResponse {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

class AuthService {
  private currentUser: UserResponse | null = null;

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      // Log login attempt
        username: credentials.username,
        text: `Login attempt for user ${credentials.username}`
      });

      const response = await apiClient.post<AuthResponse>(
        '/api/auth/login',
        credentials,
        { skipAuth: true }
      );

      // Store the token
      apiClient.setAuthToken(response.access_token);
      
      // Store user data
      this.currentUser = response.user as UserResponse;
      if (typeof window !== 'undefined') {
        localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
      }

      // Log successful login
        userId: response.user.id,
        username: response.user.username,
        text: `User ${response.user.username} logged in successfully`
      });

      return response;
    } catch (error) {
      // Log failed login
        username: credentials.username,
        error: error instanceof Error ? error.message : 'Unknown error',
        text: `Login failed for user ${credentials.username}`
      });
      throw error;
    }
  }

  async register(data: RegisterData): Promise<UserResponse> {
    try {
      // Log registration attempt
        username: data.username,
        email: data.email,
        text: `Registration attempt for user ${data.username}`
      });

      const response = await apiClient.post<UserResponse>(
        '/api/auth/register',
        data,
        { skipAuth: true }
      );

      // Log successful registration
        userId: response.id,
        username: response.username,
        text: `User ${response.username} registered successfully`
      });

      return response;
    } catch (error) {
      // Log failed registration
        username: data.username,
        error: error instanceof Error ? error.message : 'Unknown error',
        text: `Registration failed for user ${data.username}`
      });
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      // Log logout
      if (this.currentUser) {
          userId: this.currentUser.id,
          username: this.currentUser.username,
          text: `User ${this.currentUser.username} logged out`
        });
      }

      // Call logout endpoint
      await apiClient.post('/api/auth/logout');
    } catch (error) {
      // Continue with local logout even if API call fails
      console.error('Logout API call failed:', error);
    } finally {
      // Clear local state
      apiClient.setAuthToken(null);
      this.currentUser = null;
      if (typeof window !== 'undefined') {
        localStorage.removeItem('currentUser');
        localStorage.removeItem('authToken');
      }
    }
  }

  async getCurrentUser(forceRefresh: boolean = false): Promise<UserResponse | null> {
    // Return cached user if available and not forcing refresh
    if (this.currentUser && !forceRefresh) {
      return this.currentUser;
    }

    // Try to load from localStorage if not forcing refresh
    if (!forceRefresh && typeof window !== 'undefined') {
      const storedUser = localStorage.getItem('currentUser');
      if (storedUser) {
        this.currentUser = JSON.parse(storedUser);
        return this.currentUser;
      }
    }

    // If we have a token, try to fetch user data
    if (apiClient.getAuthToken()) {
      try {
        const response = await apiClient.get<UserResponse>('/api/auth/me');
        this.currentUser = response;
        if (typeof window !== 'undefined') {
          localStorage.setItem('currentUser', JSON.stringify(response));
        }
        return response;
      } catch (error) {
        // Token might be invalid, clear it
        this.logout();
        return null;
      }
    }

    return null;
  }

  async refreshToken(): Promise<void> {
    try {
      const response = await apiClient.post<AuthResponse>('/api/auth/refresh');
      apiClient.setAuthToken(response.access_token);
      
      // Log token refresh
        userId: response.user.id,
        text: `Token refreshed for user ${response.user.username}`
      });
    } catch (error) {
      // If refresh fails, logout
      await this.logout();
      throw error;
    }
  }

  isAuthenticated(): boolean {
    return !!apiClient.getAuthToken();
  }

  getUser(): UserResponse | null {
    return this.currentUser;
  }
}

// Export singleton instance
export const authService = new AuthService();

// Export types
export type { LoginCredentials, RegisterData, AuthResponse, UserResponse };
