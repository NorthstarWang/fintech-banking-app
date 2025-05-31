import { apiClient } from './client';
import { Loan, LoanApplication, LoanOffer, LoanPaymentSchedule } from '@/types';

export const loansApi = {
  // Get all loans for user
  async getLoans() {
    return apiClient.get<Loan[]>('/api/loans');
  },

  // Get specific loan details
  async getLoan(loanId: string) {
    return apiClient.get<Loan>(`/api/loans/${loanId}`);
  },

  // Get loan applications
  async getApplications() {
    return apiClient.get<LoanApplication[]>('/api/loans/applications');
  },

  // Get specific application
  async getApplication(applicationId: string) {
    return apiClient.get<LoanApplication>(`/api/loans/applications/${applicationId}`);
  },

  // Create loan application
  async createApplication(data: {
    loanType: 'personal' | 'auto' | 'mortgage' | 'student' | 'business' | 'crypto_backed';
    amount: number;
    term: number;
    purpose: string;
    employmentInfo?: {
      employer: string;
      position: string;
      income: number;
      employmentLength: number;
    };
    collateral?: {
      type: string;
      value: number;
      description: string;
    };
  }) {
    return apiClient.post<LoanApplication>('/api/loans/applications', data);
  },

  // Update application
  async updateApplication(applicationId: string, data: Partial<LoanApplication>) {
    return apiClient.put<LoanApplication>(`/api/loans/applications/${applicationId}`, data);
  },

  // Submit application for review
  async submitApplication(applicationId: string) {
    return apiClient.post<{ message: string; application: LoanApplication }>(`/api/loans/applications/${applicationId}/submit`);
  },

  // Get loan offers
  async getOffers(applicationId?: string) {
    const params = applicationId ? `?application_id=${applicationId}` : '';
    return apiClient.get<LoanOffer[]>(`/api/loans/offers${params}`);
  },

  // Get specific offer
  async getOffer(offerId: string) {
    return apiClient.get<LoanOffer>(`/api/loans/offers/${offerId}`);
  },

  // Accept loan offer
  async acceptOffer(offerId: string) {
    return apiClient.post<{ message: string; loan: Loan }>(`/api/loans/offers/${offerId}/accept`);
  },

  // Reject loan offer
  async rejectOffer(offerId: string) {
    return apiClient.post<{ message: string }>(`/api/loans/offers/${offerId}/reject`);
  },

  // Get payment schedule
  async getPaymentSchedule(loanId: string) {
    return apiClient.get<LoanPaymentSchedule[]>(`/api/loans/${loanId}/schedule`);
  },

  // Make loan payment
  async makePayment(loanId: string, data: {
    amount: number;
    paymentType: 'regular' | 'extra_principal' | 'payoff';
    accountId: string;
  }) {
    return apiClient.post<{
      message: string;
      payment: {
        id: string;
        amount: number;
        appliedToPrincipal: number;
        appliedToInterest: number;
        remainingBalance: number;
      };
    }>(`/api/loans/${loanId}/payments`, data);
  },

  // Get payment history
  async getPaymentHistory(loanId: string) {
    return apiClient.get<Array<{
      id: string;
      date: string;
      amount: number;
      principal: number;
      interest: number;
      balance: number;
      status: string;
    }>>(`/api/loans/${loanId}/payments`);
  },

  // Calculate loan details
  async calculateLoan(data: {
    amount: number;
    term: number;
    interestRate: number;
    loanType: string;
  }) {
    return apiClient.post<{
      monthlyPayment: number;
      totalInterest: number;
      totalPayment: number;
      schedule: Array<{
        month: number;
        payment: number;
        principal: number;
        interest: number;
        balance: number;
      }>;
    }>('/api/loans/calculate', data);
  },

  // Get refinance options
  async getRefinanceOptions(loanId: string) {
    return apiClient.get<Array<{
      id: string;
      lender: string;
      interestRate: number;
      term: number;
      monthlyPayment: number;
      totalSavings: number;
      closingCosts: number;
    }>>(`/api/loans/${loanId}/refinance-options`);
  },

  // Request refinance
  async requestRefinance(loanId: string, offerId: string) {
    return apiClient.post<{
      message: string;
      application: LoanApplication;
    }>(`/api/loans/${loanId}/refinance`, { offerId });
  },

  // Get loan documents
  async getDocuments(loanId: string) {
    return apiClient.get<Array<{
      id: string;
      name: string;
      type: string;
      uploadDate: string;
      size: number;
      url: string;
    }>>(`/api/loans/${loanId}/documents`);
  },

  // Upload document
  async uploadDocument(loanId: string, file: File, documentType: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('documentType', documentType);

    return apiClient.post<{
      message: string;
      document: {
        id: string;
        name: string;
        url: string;
      };
    }>(`/api/loans/${loanId}/documents`, formData, {
      headers: {}, // Let browser set content-type for FormData
    });
  },

  // Get prequalification
  async getPrequalification(data: {
    loanType: string;
    amount: number;
    creditScore?: number;
    income?: number;
  }) {
    return apiClient.post<{
      qualified: boolean;
      estimatedRate: number;
      estimatedPayment: number;
      maxAmount: number;
      reasons?: string[];
    }>('/api/loans/prequalify', data);
  },

  // Get loan summary
  async getLoanSummary() {
    return apiClient.get<{
      totalBalance: number;
      totalMonthlyPayment: number;
      nextPaymentDue: string;
      totalPaidThisYear: number;
      totalInterestPaid: number;
      loansByType: Array<{
        type: string;
        count: number;
        totalBalance: number;
      }>;
    }>('/api/loans/summary');
  }
};