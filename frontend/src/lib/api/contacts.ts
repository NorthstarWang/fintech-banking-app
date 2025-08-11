import { apiClient } from './client';

export interface Contact {
  id: number;
  user_id: number;
  contact_id: number;
  status: 'pending' | 'accepted' | 'blocked';
  nickname?: string;
  is_favorite: boolean;
  contact_username?: string;
  contact_email?: string;
  created_at: string;
  updated_at?: string;
}

export interface ContactCreate {
  contact_id: number;
  nickname?: string;
}

export interface ContactUpdate {
  nickname?: string;
  is_favorite?: boolean;
}

export interface ContactSearchResult {
  id: number;
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
}

export interface PendingRequests {
  sent_requests: Array<{
    id: number;
    contact_id: number;
    username: string;
    email: string;
    created_at: string;
  }>;
  received_requests: Array<{
    id: number;
    contact_id: number;
    username: string;
    email: string;
    created_at: string;
  }>;
}

class ContactsService {
  async createContactRequest(data: ContactCreate): Promise<Contact> {
    return apiClient.post<Contact>('/api/contacts', data);
  }

  async getContacts(status?: 'pending' | 'accepted' | 'blocked', includePending = true): Promise<Contact[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('include_pending', includePending.toString());
    
    return apiClient.get<Contact[]>(`/api/contacts?${params.toString()}`);
  }

  async getPendingRequests(): Promise<PendingRequests> {
    return apiClient.get<PendingRequests>('/api/contacts/requests/pending');
  }

  async updateContactStatus(contactId: number, status: 'accepted' | 'blocked'): Promise<Contact> {
    return apiClient.put<Contact>(`/api/contacts/${contactId}/status`, { status });
  }

  async updateContact(contactId: number, data: ContactUpdate): Promise<Contact> {
    return apiClient.put<Contact>(`/api/contacts/${contactId}`, data);
  }

  async removeContact(contactId: number): Promise<{ message: string }> {
    return apiClient.delete(`/api/contacts/${contactId}`);
  }

  async searchUsers(query: string, excludeContacts = true): Promise<ContactSearchResult[]> {
    const params = new URLSearchParams();
    params.append('q', query);
    params.append('exclude_contacts', excludeContacts.toString());
    
    return apiClient.get<ContactSearchResult[]>(`/api/contacts/search?${params.toString()}`);
  }
}

export const contactsService = new ContactsService();