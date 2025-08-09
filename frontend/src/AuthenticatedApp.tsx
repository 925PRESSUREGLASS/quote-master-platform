import React, { useState } from 'react';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { PerthSuburbSelector, ServiceTypeSelector } from './components/quotes';
import suburbsData from './data/perth-suburbs.json';
import { LogOut, User, Calculator, History, Settings } from 'lucide-react';

// Main authenticated application content
const AuthenticatedContent: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'calculator' | 'history' | 'settings'>('calculator');

  // Quote Calculator State
  const [selectedSuburb, setSelectedSuburb] = useState('');
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

  const handleLocationChange = (suburb: string, address: string) => {
    setSelectedSuburb(suburb);
    setAddress(address);
  };

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
    const suburbInfo = suburbsData.suburbs.find(s => s.name === selectedSuburb);
    if (!suburbInfo) return basePrice;
    return basePrice * suburbInfo.base_rate_multiplier;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const suburbInfo = suburbsData.suburbs.find(s => s.name === selectedSuburb);
    if (!suburbInfo) return;

    const adjustedPrice = basePrice * suburbInfo.base_rate_multiplier;
    const quoteId = `SQ-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${Math.floor(Math.random() * 10000).toString().padStart(4, '0')}`;

    const serviceNames = {
      'residential': 'Residential Glass Repair',
      'commercial': 'Commercial Glazing Services',
      'emergency': 'Emergency Glass Repair',
      'shower': 'Shower Screen Installation/Repair',
      'mirrors': 'Mirror Installation/Repair',
      'windows': 'Window Cleaning/Repair'
    };

    const selectedServiceNames = selectedServices.map(svc => serviceNames[svc as keyof typeof serviceNames] || svc);

    const newQuote = {
      id: quoteId,
      user_email: user?.email,
      suburb: selectedSuburb,
      address,
      services: selectedServices,
      service_names: selectedServiceNames,
      base_price: basePrice,
      adjusted_price: adjustedPrice,
      multiplier: suburbInfo.base_rate_multiplier,
      ai_quote: `Professional ${selectedServiceNames.join(', ')} service for your property in ${selectedSuburb}. Our experienced team will provide quality service with attention to detail.`,
      recommendation: `Based on your location in ${selectedSuburb} (Zone ${suburbInfo.zone}), we recommend our comprehensive service package.`,
      created_at: new Date().toISOString(),
      status: 'draft'
    };

    setQuoteHistory(prev => [newQuote, ...prev]);

    alert(`🎉 Quote Generated & Saved!\n\n📋 Quote ID: ${newQuote.id}\n🔧 Services: ${selectedServiceNames.join(', ')}\n📍 Location: ${selectedSuburb}\n💰 Total: $${adjustedPrice.toFixed(2)}\n\n✅ Quote saved to your account history!`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">Quote Master Pro</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <User className="w-4 h-4" />
                <span>{user?.name}</span>
              </div>
              <button
                onClick={logout}
                className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md hover:bg-gray-100"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'calculator', label: 'Quote Calculator', icon: Calculator },
              { id: 'history', label: 'Quote History', icon: History },
              { id: 'settings', label: 'Settings', icon: Settings },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'calculator' && (
          <div className="space-y-8">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Service Quote Calculator</h2>
              <p className="text-gray-600">Calculate quotes for glass and cleaning services in Perth, WA</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Location Section */}
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                <PerthSuburbSelector
                  selectedSuburb={selectedSuburb}
                  address={address}
                  suburbs={suburbsData.suburbs}
                  onChange={handleLocationChange}
                />
              </div>

              {/* Services Section */}
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                <ServiceTypeSelector
                  selectedServices={selectedServices}
                  onServiceToggle={handleServiceToggle}
                  basePrice={basePrice}
                />
              </div>

              {/* Quote Summary */}
              {basePrice > 0 && (
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="text-lg font-semibold text-blue-900 mb-4">Quote Summary</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Base Price:</span>
                      <span className="font-medium">${basePrice.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Location Adjustment:</span>
                      <span className="font-medium">
                        {selectedSuburb
                          ? `${(suburbsData.suburbs.find(s => s.name === selectedSuburb)?.base_rate_multiplier || 1).toFixed(2)}x`
                          : 'Not selected'}
                      </span>
                    </div>
                    <div className="border-t border-blue-200 mt-2 pt-2 flex justify-between">
                      <span className="text-blue-900 font-medium">Estimated Total:</span>
                      <span className="text-blue-900 font-bold">
                        ${calculateAdjustedPrice().toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                disabled={!selectedSuburb || !address || selectedServices.length === 0}
              >
                Generate & Save Quote
              </button>
            </form>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Quote History</h2>
            {quoteHistory.length === 0 ? (
              <div className="bg-white rounded-lg p-8 text-center border border-gray-200">
                <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No quotes yet</h3>
                <p className="text-gray-600">Generate your first quote to see it here!</p>
              </div>
            ) : (
              <div className="space-y-4">
                {quoteHistory.map((quote) => (
                  <div key={quote.id} className="bg-white rounded-lg p-6 border border-gray-200">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">Quote {quote.id}</h3>
                        <p className="text-sm text-gray-600">
                          {new Date(quote.created_at).toLocaleDateString()} at {new Date(quote.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                      <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                        {quote.status}
                      </span>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Location</p>
                        <p className="font-medium">{quote.suburb}</p>
                        <p className="text-sm text-gray-500">{quote.address}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Services</p>
                        <p className="font-medium">{quote.service_names.join(', ')}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Total Price</p>
                        <p className="text-xl font-bold text-green-600">${quote.adjusted_price.toFixed(2)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Account Settings</h2>
            <div className="bg-white rounded-lg p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name</label>
                  <p className="mt-1 text-sm text-gray-900">{user?.name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Account Created</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

// Authentication wrapper component
const AuthWrapper: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const { login, register } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          {authMode === 'login' ? (
            <LoginForm
              onLogin={login}
              onSwitchToRegister={() => setAuthMode('register')}
            />
          ) : (
            <RegisterForm
              onRegister={register}
              onSwitchToLogin={() => setAuthMode('login')}
            />
          )}
        </div>
      </div>
    );
  }

  return <AuthenticatedContent />;
};

// Main app component
const AuthenticatedApp: React.FC = () => {
  return (
    <AuthProvider>
      <AuthWrapper />
    </AuthProvider>
  );
};

export default AuthenticatedApp;
