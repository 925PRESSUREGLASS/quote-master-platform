/**
 * Quote Management Page
 * Main page for managing service quotes with all calculator components
 */

import React, { useState } from 'react';
import { Calculator, History, Plus } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ServiceQuoteCalculator } from '@/components/quotes';
import { ServiceQuote } from '@/types';

export const QuoteManagementPage: React.FC = () => {
  const [activeView, setActiveView] = useState<'calculator' | 'history' | 'templates'>('calculator');
  const [recentQuotes, setRecentQuotes] = useState<ServiceQuote[]>([]);

  const views = [
    {
      key: 'calculator' as const,
      label: 'Quote Calculator',
      description: 'Create new service quotes',
      icon: Calculator,
      color: 'text-blue-600'
    },
    {
      key: 'history' as const,
      label: 'Quote History',
      description: 'View and manage existing quotes',
      icon: History,
      color: 'text-green-600'
    },
    {
      key: 'templates' as const,
      label: 'Quote Templates',
      description: 'Manage quote templates',
      icon: Plus,
      color: 'text-purple-600'
    }
  ];

  const handleQuoteCreated = (quote: ServiceQuote) => {
    setRecentQuotes(prev => [quote, ...prev.slice(0, 4)]);
  };

  const renderActiveView = () => {
    switch (activeView) {
      case 'calculator':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Service Quote Calculator</h2>
              <p className="text-gray-600">
                Create professional quotes for window cleaning and pressure washing services in Perth.
              </p>
            </div>
            <ServiceQuoteCalculator onQuoteCreated={handleQuoteCreated} />
          </div>
        );
      
      case 'history':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Quote History</h2>
              <p className="text-gray-600">
                View and manage all your service quotes.
              </p>
            </div>
            
            {recentQuotes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {recentQuotes.map((quote) => (
                  <Card key={quote.id} className="p-4">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <h3 className="font-semibold text-sm">{quote.customer_name}</h3>
                        <span className="text-xs text-gray-500">
                          {new Date(quote.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        <div>{quote.service_type.replace('_', ' ')} - {quote.suburb}</div>
                        <div>{quote.square_meters}m² • {quote.stories} {quote.stories === 1 ? 'story' : 'stories'}</div>
                      </div>
                      <div className="flex justify-between items-center pt-2 border-t">
                        <span className="font-semibold text-green-600">
                          ${quote.pricing_breakdown.final_total.toFixed(2)}
                        </span>
                        <Button size="sm" variant="outline">
                          View Details
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="p-8 text-center">
                <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Quotes Yet</h3>
                <p className="text-gray-600 mb-4">
                  Start creating quotes to see them here.
                </p>
                <Button onClick={() => setActiveView('calculator')}>
                  Create Your First Quote
                </Button>
              </Card>
            )}
          </div>
        );
      
      case 'templates':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Quote Templates</h2>
              <p className="text-gray-600">
                Create and manage reusable quote templates for common services.
              </p>
            </div>
            
            <Card className="p-8 text-center">
              <Plus className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Templates Coming Soon</h3>
              <p className="text-gray-600 mb-4">
                Save frequently used quote configurations as templates for quick access.
              </p>
              <Button disabled>
                Create Template
              </Button>
            </Card>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Quote Management</h1>
                <p className="mt-2 text-gray-600">
                  Professional service quotes for Perth window cleaning and pressure washing
                </p>
              </div>
              
              {/* Quick Stats */}
              <div className="hidden lg:flex items-center space-x-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{recentQuotes.length}</div>
                  <div className="text-xs text-gray-500">Recent Quotes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    ${recentQuotes.reduce((sum, q) => sum + q.pricing_breakdown.final_total, 0).toFixed(0)}
                  </div>
                  <div className="text-xs text-gray-500">Total Value</div>
                </div>
              </div>
            </div>
            
            {/* Navigation Tabs */}
            <div className="mt-6">
              <nav className="flex space-x-6">
                {views.map((view) => {
                  const Icon = view.icon;
                  return (
                    <button
                      key={view.key}
                      onClick={() => setActiveView(view.key)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                        activeView === view.key
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${activeView === view.key ? 'text-blue-600' : view.color}`} />
                      {view.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderActiveView()}
      </div>

      {/* Quick Actions Sidebar - Mobile */}
      <div className="fixed bottom-6 right-6 lg:hidden">
        <Button
          onClick={() => setActiveView('calculator')}
          className="rounded-full w-14 h-14 shadow-lg"
          size="lg"
        >
          <Calculator className="w-6 h-6" />
        </Button>
      </div>
    </div>
  );
};
