interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
}

class AuthService {
  private readonly baseUrl = 'http://localhost:8000/api/v1';
  private readonly tokenKey = 'quote_master_token';
  private readonly userKey = 'quote_master_user';

  async login(email: string, password: string): Promise<AuthResponse> {
    // Demo mode - simulate API call
    if (email === 'demo@example.com' && password === 'demo123') {
      const mockResponse: AuthResponse = {
        user: {
          id: '1',
          name: 'Demo User',
          email: 'demo@example.com',
          created_at: new Date().toISOString()
        },
        access_token: 'demo_token_' + Math.random(),
        token_type: 'bearer'
      };

      // Store in localStorage
      localStorage.setItem(this.tokenKey, mockResponse.access_token);
      localStorage.setItem(this.userKey, JSON.stringify(mockResponse.user));

      return mockResponse;
    }

    // For real API integration (currently disabled)
    /*
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: email,
        password: password,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    localStorage.setItem(this.tokenKey, data.access_token);
    localStorage.setItem(this.userKey, JSON.stringify(data.user));

    return data;
    */

    throw new Error('Invalid credentials. Use demo@example.com / demo123');
  }

  async register(name: string, email: string, password: string): Promise<AuthResponse> {
    // Demo mode - simulate registration
    const mockResponse: AuthResponse = {
      user: {
        id: Math.random().toString(),
        name,
        email,
        created_at: new Date().toISOString()
      },
      access_token: 'demo_token_' + Math.random(),
      token_type: 'bearer'
    };

    // Store in localStorage
    localStorage.setItem(this.tokenKey, mockResponse.access_token);
    localStorage.setItem(this.userKey, JSON.stringify(mockResponse.user));

    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    return mockResponse;

    // For real API integration (currently disabled)
    /*
    const response = await fetch(`${this.baseUrl}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name,
        email,
        password,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data = await response.json();
    localStorage.setItem(this.tokenKey, data.access_token);
    localStorage.setItem(this.userKey, JSON.stringify(data.user));

    return data;
    */
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem(this.userKey);
    return userStr ? JSON.parse(userStr) : null;
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

export const authService = new AuthService();
export type { User, AuthResponse };
