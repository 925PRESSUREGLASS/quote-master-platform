import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';
import { User, LoginCredentials, RegisterCredentials } from '@/types';
import { authService } from '@/services/auth';
import { useAnalytics } from '@/hooks/useAnalytics';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { trackEvent } = useAnalytics();

  const isAuthenticated = !!user;

  // Initialize auth state
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      if (authService.isAuthenticated()) {
        // Validate token and get current user
        const isValid = await authService.validateToken();
        if (isValid) {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
        } else {
          // Token is invalid, clear auth
          authService.clearAuth();
        }
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      authService.clearAuth();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials) => {
    try {
      setIsLoading(true);
      const response = await authService.login(credentials);
      setUser(response.user);

      // Track login event
      trackEvent('user_login', {
        user_id: response.user.id,
        login_method: 'email',
        remember_me: credentials.remember_me || false,
      });

      toast.success(`Welcome back, ${response.user.display_name}!`);
    } catch (error: any) {
      console.error('Login failed:', error);
      toast.error(error.detail || 'Login failed. Please try again.');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (credentials: RegisterCredentials) => {
    try {
      setIsLoading(true);
      const newUser = await authService.register(credentials);

      // Track registration event
      trackEvent('user_register', {
        user_id: newUser.id,
        registration_method: 'email',
      });

      toast.success(
        'Registration successful! Please check your email to verify your account.'
      );
    } catch (error: any) {
      console.error('Registration failed:', error);
      toast.error(error.detail || 'Registration failed. Please try again.');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);

      // Track logout event
      if (user) {
        trackEvent('user_logout', {
          user_id: user.id,
          session_duration: Date.now(), // This would be calculated properly
        });
      }

      await authService.logout();
      setUser(null);
      toast.success('You have been logged out successfully.');
    } catch (error: any) {
      console.error('Logout failed:', error);
      // Still clear user state even if API call fails
      setUser(null);
      authService.clearAuth();
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (data: Partial<User>) => {
    try {
      const updatedUser = await authService.updateProfile(data);
      setUser(updatedUser);
      toast.success('Profile updated successfully!');
    } catch (error: any) {
      console.error('Profile update failed:', error);
      toast.error(error.detail || 'Failed to update profile.');
      throw error;
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If refresh fails, user might be logged out
      setUser(null);
      authService.clearAuth();
    }
  };

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    updateProfile,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export { AuthContext };