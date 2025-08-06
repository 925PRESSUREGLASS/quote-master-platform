/**
 * Quote service for frontend API integration
 * Handles all quote-related operations including service quotes and inspirational quotes
 */

import { apiService } from './api';
import { 
  Quote, 
  ServiceQuote,
  QuoteGeneration, 
  ServiceQuoteRequest,
  ServiceQuoteCalculation,
  PaginatedResponse,
  ServiceQuoteStatus
} from '@/types';

export class QuoteService {
  private static instance: QuoteService;
  
  public static getInstance(): QuoteService {
    if (!QuoteService.instance) {
      QuoteService.instance = new QuoteService();
    }
    return QuoteService.instance;
  }

  // Inspirational Quotes
  async generateQuote(data: QuoteGeneration): Promise<Quote> {
    try {
      return await apiService.post<Quote>('/quotes/generate', data);
    } catch (error) {
      console.error('Failed to generate quote:', error);
      throw error;
    }
  }

  async getQuotes(params?: {
    page?: number;
    limit?: number;
    category?: string;
    search?: string;
  }): Promise<PaginatedResponse<Quote>> {
    try {
      return await apiService.get<PaginatedResponse<Quote>>('/quotes', { params });
    } catch (error) {
      console.error('Failed to fetch quotes:', error);
      throw error;
    }
  }

  async getQuoteById(id: string): Promise<Quote> {
    try {
      return await apiService.get<Quote>(`/quotes/${id}`);
    } catch (error) {
      console.error(`Failed to fetch quote ${id}:`, error);
      throw error;
    }
  }

  async favoriteQuote(id: string): Promise<void> {
    try {
      await apiService.post(`/quotes/${id}/favorite`);
    } catch (error) {
      console.error(`Failed to favorite quote ${id}:`, error);
      throw error;
    }
  }

  async unfavoriteQuote(id: string): Promise<void> {
    try {
      await apiService.delete(`/quotes/${id}/favorite`);
    } catch (error) {
      console.error(`Failed to unfavorite quote ${id}:`, error);
      throw error;
    }
  }

  // Service Quotes (Window/Pressure Cleaning)
  async calculateServiceQuote(data: ServiceQuoteCalculation): Promise<ServiceQuote> {
    try {
      return await apiService.post<ServiceQuote>('/api/v1/service-quotes/calculate', data);
    } catch (error) {
      console.error('Failed to calculate service quote:', error);
      throw error;
    }
  }

  async createServiceQuote(data: ServiceQuoteRequest): Promise<ServiceQuote> {
    try {
      return await apiService.post<ServiceQuote>('/api/v1/service-quotes/', data);
    } catch (error) {
      console.error('Failed to create service quote:', error);
      throw error;
    }
  }

  async getServiceQuotes(params?: {
    page?: number;
    limit?: number;
    status?: ServiceQuoteStatus;
    service_type?: string;
    property_type?: string;
    suburb?: string;
  }): Promise<PaginatedResponse<ServiceQuote>> {
    try {
      return await apiService.get<PaginatedResponse<ServiceQuote>>('/api/v1/service-quotes/', { params });
    } catch (error) {
      console.error('Failed to fetch service quotes:', error);
      throw error;
    }
  }

  async getServiceQuoteById(id: string): Promise<ServiceQuote> {
    try {
      return await apiService.get<ServiceQuote>(`/api/v1/service-quotes/${id}`);
    } catch (error) {
      console.error(`Failed to fetch service quote ${id}:`, error);
      throw error;
    }
  }

  async updateServiceQuoteStatus(id: string, status: ServiceQuoteStatus): Promise<ServiceQuote> {
    try {
      return await apiService.put<ServiceQuote>(`/api/v1/service-quotes/${id}/status`, { status });
    } catch (error) {
      console.error(`Failed to update service quote ${id} status:`, error);
      throw error;
    }
  }

  async recalculateServiceQuote(id: string): Promise<ServiceQuote> {
    try {
      return await apiService.post<ServiceQuote>(`/api/v1/service-quotes/${id}/recalculate`);
    } catch (error) {
      console.error(`Failed to recalculate service quote ${id}:`, error);
      throw error;
    }
  }

  async createServiceQuoteFromVoice(audioFile: File, additionalData?: Partial<ServiceQuoteRequest>): Promise<ServiceQuote> {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      
      if (additionalData) {
        formData.append('additional_data', JSON.stringify(additionalData));
      }

      return await apiService.post<ServiceQuote>('/api/v1/service-quotes/from-voice', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
    } catch (error) {
      console.error('Failed to create service quote from voice:', error);
      throw error;
    }
  }

  // Enums and Reference Data
  async getServiceTypes(): Promise<string[]> {
    try {
      const response = await apiService.get<{ service_types: string[] }>('/api/v1/service-quotes/enums/service-types');
      return response.service_types;
    } catch (error) {
      console.error('Failed to fetch service types:', error);
      throw error;
    }
  }

  async getPropertyTypes(): Promise<string[]> {
    try {
      const response = await apiService.get<{ property_types: string[] }>('/api/v1/service-quotes/enums/property-types');
      return response.property_types;
    } catch (error) {
      console.error('Failed to fetch property types:', error);
      throw error;
    }
  }

  async getSuburbs(): Promise<Array<{ name: string; zone: string; base_rate_multiplier: number }>> {
    try {
      const response = await apiService.get<{ suburbs: Array<{ name: string; zone: string; base_rate_multiplier: number }> }>('/api/v1/service-quotes/enums/suburbs');
      return response.suburbs;
    } catch (error) {
      console.error('Failed to fetch suburbs:', error);
      throw error;
    }
  }

  async getQuoteStatuses(): Promise<string[]> {
    try {
      const response = await apiService.get<{ statuses: string[] }>('/api/v1/service-quotes/enums/quote-statuses');
      return response.statuses;
    } catch (error) {
      console.error('Failed to fetch quote statuses:', error);
      throw error;
    }
  }

  // Analytics
  async getServiceQuoteAnalytics(): Promise<{
    total_quotes: number;
    total_value: number;
    average_quote_value: number;
    quotes_by_status: Record<string, number>;
    quotes_by_service_type: Record<string, number>;
    quotes_by_suburb_zone: Record<string, number>;
    monthly_trends: Array<{ month: string; count: number; value: number }>;
  }> {
    try {
      return await apiService.get('/api/v1/service-quotes/analytics/summary');
    } catch (error) {
      console.error('Failed to fetch service quote analytics:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const quoteService = QuoteService.getInstance();
