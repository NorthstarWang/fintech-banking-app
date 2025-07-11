import { apiClient } from './client';

export interface P2PContact {
  id: string;
  name: string;
  username: string;
  email: string;
  phone: string;
  avatar?: string;
  is_favorite: boolean;
  last_transaction?: {
    date: string;
    amount: number;
    type: 'sent' | 'received';
  };
}

export interface P2PTransferRequest {
  recipient_id: string;
  amount: number;
  description?: string;
  method: 'instant' | 'standard';
  source_account_id: string;
}

export interface P2PTransferResponse {
  transaction_id: string;
  amount: number;
  fee: number;
  total_amount: number;
  status: string;
  method: string;
}

export interface P2PSplitPaymentRequest {
  total_amount: number;
  participants: string[];
  split_type: 'equal' | 'percentage' | 'amount';
  split_details?: Record<string, number>;
  description: string;
  source_account_id: string;
}

export interface P2PSplitPaymentResponse {
  split_id: string;
  total_amount: number;
  participant_amounts: Record<string, number>;
  payment_requests: Array<{
    id: string;
    requester_id: string;
    payer_id: string;
    amount: number;
    description: string;
    status: string;
    created_at: string;
  }>;
  status: string;
}

export interface P2PPaymentRequest {
  requester_id: string;
  amount: number;
  description: string;
  due_date?: string;
}

export interface P2PQRCodeResponse {
  qr_code: string;
  payment_link: string;
  expires_at: string;
}

export const p2pApi = {
  // Get P2P contacts
  getContacts: async (): Promise<P2PContact[]> => {
    return await apiClient.get('/api/p2p/contacts');
  },

  // Create P2P transfer
  createTransfer: async (data: P2PTransferRequest): Promise<P2PTransferResponse> => {
    return await apiClient.post('/api/p2p/transfer', data);
  },

  // Create split payment
  createSplitPayment: async (data: P2PSplitPaymentRequest): Promise<P2PSplitPaymentResponse> => {
    return await apiClient.post('/api/p2p/split-payment', data);
  },

  // Create payment request
  createPaymentRequest: async (data: P2PPaymentRequest): Promise<any> => {
    return await apiClient.post('/api/p2p/payment-request', data);
  },

  // Generate QR code
  generateQRCode: async (amount?: number, description?: string): Promise<P2PQRCodeResponse> => {
    const params = new URLSearchParams();
    if (amount) params.append('amount', amount.toString());
    if (description) params.append('description', description);
    
    return await apiClient.get(`/api/p2p/qr-code?${params.toString()}`);
  },

  // Scan QR code
  scanQRCode: async (qrData: any): Promise<any> => {
    return await apiClient.post('/api/p2p/scan-qr', qrData);
  },

  // Get payment requests
  getPaymentRequests: async (): Promise<any[]> => {
    return await apiClient.get('/api/p2p/payment-requests');
  },

  // Accept payment request
  acceptPaymentRequest: async (requestId: string, accountId: string): Promise<any> => {
    const response = await apiClient.post(`/api/p2p/payment-requests/${requestId}/accept`, {
      source_account_id: accountId
    });
    return response.data;
  },

  // Decline payment request
  declinePaymentRequest: async (requestId: string): Promise<any> => {
    const response = await apiClient.post(`/api/p2p/payment-requests/${requestId}/decline`);
    return response.data;
  }
};