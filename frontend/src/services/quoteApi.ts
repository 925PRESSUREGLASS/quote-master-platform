import { ApiService } from './api';
import { SuburbInfo } from '@/components/quotes/PerthSuburbSelector';

// Quote Request Types
export interface CreateQuoteRequest {
  suburb: string;
  address: string;
  services: string[];
  base_price: number;
  adjusted_price: number;
  multiplier: number;
  notes?: string;
  customer_details?: {
    name?: string;
    email?: string;
    phone?: string;
  };
}

export interface QuoteResponse {
  id: string;
  quote_number: string;
  suburb: string;
  address: string;
  services: string[];
  base_price: number;
  adjusted_price: number;
  multiplier: number;
  notes?: string;
  status: 'draft' | 'pending' | 'approved' | 'sent' | 'expired';
  valid_until: string;
  created_at: string;
  updated_at?: string;
  customer_details?: {
    name?: string;
    email?: string;
    phone?: string;
  };
}

export interface UpdateQuoteRequest {
  services?: string[];
  base_price?: number;
  adjusted_price?: number;
  notes?: string;
  status?: 'draft' | 'pending' | 'approved' | 'sent' | 'expired';
  customer_details?: {
    name?: string;
    email?: string;
    phone?: string;
  };
}

export interface QuoteListResponse {
  quotes: QuoteResponse[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface SuburbValidationRequest {
  suburb: string;
  address: string;
}

export interface SuburbValidationResponse {
  is_valid: boolean;
  validated_address: string;
  suburb_info: SuburbInfo;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  distance_from_base?: number;
  estimated_travel_time?: number;
}

export interface ServicePricingResponse {
  services: Array<{
    id: string;
    name: string;
    description: string;
    base_price: number;
    category: string;
    is_active: boolean;
  }>;
}

export interface EmailQuoteRequest {
  quote_id: string;
  recipient_email: string;
  message?: string;
}

export interface GeneratePdfRequest {
  quote_id: string;
  include_terms?: boolean;
  include_company_info?: boolean;
}

export interface PdfResponse {
  pdf_url: string;
  expires_at: string;
}

// Quote API Service
export class QuoteApiService {
  constructor(private apiService: ApiService) {}

  // Create a new quote
  async createQuote(data: CreateQuoteRequest): Promise<QuoteResponse> {
    return this.apiService.post<QuoteResponse>('/quotes/', data);
  }

  // Get quote by ID
  async getQuote(quoteId: string): Promise<QuoteResponse> {
    return this.apiService.get<QuoteResponse>(`/quotes/${quoteId}`);
  }

  // Update quote
  async updateQuote(quoteId: string, data: UpdateQuoteRequest): Promise<QuoteResponse> {
    return this.apiService.put<QuoteResponse>(`/quotes/${quoteId}`, data);
  }

  // Delete quote
  async deleteQuote(quoteId: string): Promise<void> {
    return this.apiService.delete(`/quotes/${quoteId}`);
  }

  // Get user quotes with pagination
  async getUserQuotes(page = 1, perPage = 10): Promise<QuoteListResponse> {
    return this.apiService.get<QuoteListResponse>(`/quotes/`, {
      params: { page, per_page: perPage }
    });
  }

  // Validate suburb and address
  async validateSuburb(data: SuburbValidationRequest): Promise<SuburbValidationResponse> {
    return this.apiService.post<SuburbValidationResponse>('/quotes/validate-suburb', data);
  }

  // Get available services and pricing
  async getServicePricing(): Promise<ServicePricingResponse> {
    return this.apiService.get<ServicePricingResponse>('/quotes/services');
  }

  // Get suburb information and pricing zones
  async getSuburbs(): Promise<{ suburbs: SuburbInfo[] }> {
    return this.apiService.get<{ suburbs: SuburbInfo[] }>('/quotes/suburbs');
  }

  // Email quote to customer
  async emailQuote(data: EmailQuoteRequest): Promise<{ success: boolean; message: string }> {
    return this.apiService.post<{ success: boolean; message: string }>(`/quotes/email`, data);
  }

  // Generate PDF quote
  async generatePdf(data: GeneratePdfRequest): Promise<PdfResponse> {
    return this.apiService.post<PdfResponse>('/quotes/generate-pdf', data);
  }

  // Submit quote for approval
  async submitQuote(quoteId: string): Promise<QuoteResponse> {
    return this.apiService.post<QuoteResponse>(`/quotes/${quoteId}/submit`);
  }

  // Calculate pricing based on services and location
  async calculatePricing(data: {
    services: string[];
    suburb: string;
    address: string;
  }): Promise<{
    base_price: number;
    adjusted_price: number;
    multiplier: number;
    breakdown: Array<{
      service: string;
      price: number;
    }>;
  }> {
    return this.apiService.post('/quotes/calculate', data);
  }
}

// Export singleton instance
import api from './api';
const apiService = new ApiService(api);
export const quoteApiService = new QuoteApiService(apiService);
