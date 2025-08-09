import React, { useState } from 'react';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Simple service selection component
const SimpleServiceSelector: React.FC<{
  services: Array<{ id: string; name: string; basePrice: number }>;
  selectedServices: string[];
  onServiceToggle: (id: string) => void;
  basePrice: number;
}> = ({ services, selectedServices, onServiceToggle, basePrice }) => {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900">Select Services</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map(service => (
          <div
            key={service.id}
            className={`p-4 rounded-lg border cursor-pointer transition-colors ${
              selectedServices.includes(service.id)
                ? 'bg-blue-50 border-blue-200'
                : 'bg-white border-gray-200 hover:border-blue-200'
            }`}
            onClick={() => onServiceToggle(service.id)}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-900">{service.name}</span>
              <span className="text-sm text-gray-600">${service.basePrice}</span>
            </div>
          </div>
        ))}
      </div>
      {basePrice > 0 && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg">
          <p className="text-green-800 font-medium">Base Total: ${basePrice}</p>
        </div>
      )}
    </div>
  );
};

// Login/Register component
const AuthForm: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(name, email, password);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Quote Master Pro</h1>
          <p className="mt-2 text-sm text-gray-600">
            Professional Glass & Cleaning Services - Perth WA
          </p>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-6">
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                isLogin
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                !isLogin
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-3 py-2 rounded text-sm">
                {error}
              </div>
            )}

            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter your name"
                  required={!isLogin}
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your email"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your password"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Please wait...' : (isLogin ? 'Login' : 'Register')}
            </button>
          </form>

          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded text-center">
            <p className="text-xs text-green-700 font-medium">Demo Credentials:</p>
            <p className="text-xs text-green-600">demo@example.com / demo123</p>
            <button
              onClick={() => {
                setEmail('demo@example.com');
                setPassword('demo123');
                setIsLogin(true);
              }}
              className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline"
            >
              Click to fill demo credentials
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main authenticated application content
const AuthenticatedContent: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'calculator' | 'history'>('calculator');

  // Quote Calculator State
  const [selectedSuburb, setSelectedSuburb] = useState('Perth');
  const [address, setAddress] = useState('');
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [basePrice, setBasePrice] = useState(0);
  const [quoteHistory, setQuoteHistory] = useState<any[]>([]);

  const services = [
    { id: 'residential', name: 'Residential Glass', basePrice: 150 },
    { id: 'commercial', name: 'Commercial Glazing', basePrice: 250 },
    { id: 'emergency', name: 'Emergency Service', basePrice: 350 },
    { id: 'shower', name: 'Shower Screens', basePrice: 200 },
    { id: 'mirrors', name: 'Mirrors', basePrice: 180 },
    { id: 'windows', name: 'Window Repairs', basePrice: 160 }
  ];

  const perthSuburbs = [
    { name: 'Perth', multiplier: 1.0 },
    { name: 'Fremantle', multiplier: 1.15 },
    { name: 'Cottesloe', multiplier: 1.25 },
    { name: 'Subiaco', multiplier: 1.10 },
    { name: 'Joondalup', multiplier: 1.20 },
    { name: 'Rockingham', multiplier: 1.15 }
  ];

  const handleServiceToggle = (serviceId: string) => {
    setSelectedServices(prev => {
      const newServices = prev.includes(serviceId)
        ? prev.filter(id => id !== serviceId)
        : [...prev, serviceId];

      const newBasePrice = services
        .filter(service => newServices.includes(service.id))
        .reduce((sum, service) => sum + service.basePrice, 0);

      setBasePrice(newBasePrice);
      return newServices;
    });
  };

  const calculateAdjustedPrice = () => {
    const suburb = perthSuburbs.find(s => s.name === selectedSuburb);
    return basePrice * (suburb?.multiplier || 1.0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedServices.length === 0) {
      alert('Please select at least one service');
      return;
    }

    const adjustedPrice = calculateAdjustedPrice();
    const quoteId = `QMP-${Date.now()}`;

    const newQuote = {
      id: quoteId,
      user: user?.name,
      suburb: selectedSuburb,
      address,
      services: selectedServices,
      basePrice,
      adjustedPrice,
      created: new Date().toLocaleString()
    };

    setQuoteHistory(prev => [newQuote, ...prev]);
    alert(`Quote Generated!\nID: ${quoteId}\nTotal: $${adjustedPrice.toFixed(2)}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Quote Master Pro</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user?.name}</span>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="mt-4">
            <div className="flex space-x-8">
              <button
                onClick={() => setActiveTab('calculator')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'calculator'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Quote Calculator
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'history'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Quote History ({quoteHistory.length})
              </button>
            </div>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4">
        {activeTab === 'calculator' ? (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-6">Service Quote Calculator</h2>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Location */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Perth Suburb
                </label>
                <select
                  value={selectedSuburb}
                  onChange={(e) => setSelectedSuburb(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {perthSuburbs.map(suburb => (
                    <option key={suburb.name} value={suburb.name}>
                      {suburb.name} (x{suburb.multiplier})
                    </option>
                  ))}
                </select>
              </div>

              {/* Address */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Property Address
                </label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Enter property address"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Services */}
              <SimpleServiceSelector
                services={services}
                selectedServices={selectedServices}
                onServiceToggle={handleServiceToggle}
                basePrice={basePrice}
              />

              {/* Price Summary */}
              {basePrice > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-gray-600">Base Price: ${basePrice}</p>
                      <p className="text-sm text-gray-600">Suburb Multiplier: x{perthSuburbs.find(s => s.name === selectedSuburb)?.multiplier}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-blue-600">
                        ${calculateAdjustedPrice().toFixed(2)}
                      </p>
                      <p className="text-sm text-gray-500">Total Quote</p>
                    </div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={selectedServices.length === 0}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-300"
              >
                Generate Quote
              </button>
            </form>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-6">Quote History</h2>
            {quoteHistory.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No quotes generated yet</p>
            ) : (
              <div className="space-y-4">
                {quoteHistory.map(quote => (
                  <div key={quote.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-gray-900">{quote.id}</h3>
                        <p className="text-sm text-gray-600">{quote.suburb} - {quote.address}</p>
                        <p className="text-sm text-gray-600">Services: {quote.services.length}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold text-green-600">
                          ${quote.adjustedPrice.toFixed(2)}
                        </p>
                        <p className="text-xs text-gray-500">{quote.created}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

// Root component
const AuthenticatedApp: React.FC = () => {
  return (
    <AuthProvider>
      <AuthContent />
    </AuthProvider>
  );
};

// Auth wrapper
const AuthContent: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return user ? <AuthenticatedContent /> : <AuthForm />;
};

export default AuthenticatedApp;
