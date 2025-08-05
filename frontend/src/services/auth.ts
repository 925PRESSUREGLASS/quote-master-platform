import {
  User,
  LoginCredentials,
  RegisterCredentials,
  AuthResponse,
} from '@/types';
import { apiService, TokenStorage } from './api';

export class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiService.post<AuthResponse>(
      '/auth/login',
      credentials
    );

    // Store tokens
    TokenStorage.setTokens(response);

    return response;
  }

  async register(credentials: RegisterCredentials): Promise<User> {
    return apiService.post<User>('/auth/register', credentials);
  }

  async logout(): Promise<void> {
    try {
      await apiService.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      TokenStorage.clearTokens();
    }
  }

  async getCurrentUser(): Promise<User> {
    return apiService.get<User>('/auth/me');
  }

  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = TokenStorage.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiService.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    TokenStorage.setTokens(response);
    return response;
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    return apiService.put<User>('/users/me', data);
  }

  async changePassword(data: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }): Promise<void> {
    return apiService.post('/auth/password/change', data);
  }

  async requestPasswordReset(email: string): Promise<void> {
    return apiService.post('/auth/password/reset-request', { email });
  }

  async confirmPasswordReset(data: {
    token: string;
    new_password: string;
    confirm_password: string;
  }): Promise<void> {
    return apiService.post('/auth/password/reset-confirm', data);
  }

  async requestEmailVerification(email: string): Promise<void> {
    return apiService.post('/auth/email/verify-request', { email });
  }

  async confirmEmailVerification(token: string): Promise<void> {
    return apiService.post('/auth/email/verify-confirm', { token });
  }

  async validateToken(): Promise<boolean> {
    try {
      await apiService.post('/auth/validate-token');
      return true;
    } catch {
      return false;
    }
  }

  isAuthenticated(): boolean {
    return !!TokenStorage.getAccessToken();
  }

  getAccessToken(): string | null {
    return TokenStorage.getAccessToken();
  }

  clearAuth(): void {
    TokenStorage.clearTokens();
  }
}

export const authService = new AuthService();