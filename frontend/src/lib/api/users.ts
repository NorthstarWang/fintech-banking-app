import { apiClient } from './client';

export interface UserSearchResult {
  id: number;
  username: string;
  full_name: string;
  email: string;
}

export interface UserProfile {
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  currency: string;
  timezone: string;
  is_active: boolean;
  last_login?: string;
}

export interface UserUpdate {
  email?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  currency?: string;
  timezone?: string;
}

export const usersService = {
  async searchUsers(query: string): Promise<UserSearchResult[]> {
    if (!query || query.length < 2) {
      return [];
    }
    
    return apiClient.get<UserSearchResult[]>(`/api/users/search?query=${encodeURIComponent(query)}`);
  },
  
  async getCurrentUser(): Promise<UserProfile> {
    return apiClient.get<UserProfile>('/api/users/me');
  },
  
  async updateProfile(data: UserUpdate): Promise<UserProfile> {
    return apiClient.put<UserProfile>('/api/users/me', data);
  },
};