import { apiClient } from './client';

export interface Category {
  id: number;
  name: string;
  type: 'INCOME' | 'EXPENSE';
  icon?: string;
  color?: string;
  is_system: boolean;
  parent_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface CategoryCreate {
  name: string;
  type: 'INCOME' | 'EXPENSE';
  icon?: string;
  color?: string;
  parent_id?: number;
}

export interface CategoryUpdate {
  name?: string;
  icon?: string;
  color?: string;
  parent_id?: number;
}

export interface CategoryStats {
  total_transactions: number;
  total_amount: number;
  average_amount: number;
  last_used: string;
}

class CategoriesService {
  async getCategories(type?: 'INCOME' | 'EXPENSE'): Promise<Category[]> {
    const params = new URLSearchParams();
    if (type) {
      params.append('type', type);
    }
    
    const queryString = params.toString();
    const url = queryString ? `/api/categories?${queryString}` : '/api/categories';
    return apiClient.get<Category[]>(url);
  }

  async getCategory(id: number): Promise<Category> {
    return apiClient.get<Category>(`/api/categories/${id}`);
  }

  async createCategory(data: CategoryCreate): Promise<Category> {
    return apiClient.post<Category>('/api/categories', data);
  }

  async updateCategory(id: number, data: CategoryUpdate): Promise<Category> {
    return apiClient.put<Category>(`/api/categories/${id}`, data);
  }

  async deleteCategory(id: number): Promise<void> {
    return apiClient.delete<void>(`/api/categories/${id}`);
  }

  async getCategoryStats(id: number): Promise<CategoryStats> {
    return apiClient.get<CategoryStats>(`/api/categories/${id}/stats`);
  }
}

// Export singleton instance
export const categoriesService = new CategoriesService();