/**
 * Quote Management Page
 * Main page for managing service quotes with all calculator components
 */

import React from 'react';
import { QuoteCalculator } from '@/components/quotes';

export const QuoteManagementPage: React.FC = () => {
  const handleQuoteSubmit = (quoteData: any) => {
    console.log('Quote submitted:', quoteData);
    alert('Quote generated successfully! Check the console for details.');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Service Quote Calculator</h1>
          <p className="mt-2 text-gray-600">Calculate quotes for glass and cleaning services in Perth, WA</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <QuoteCalculator onSubmit={handleQuoteSubmit} />
        </div>
      </div>
    </div>
  );
};
