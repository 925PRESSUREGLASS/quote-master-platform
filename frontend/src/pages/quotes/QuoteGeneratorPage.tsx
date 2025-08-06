import { useState } from 'react';
import { QuoteCalculator, QuoteData } from '@/components/quotes/QuoteCalculator';
import { Check } from 'lucide-react';

export default function QuoteGeneratorPage() {
  const [quote, setQuote] = useState<QuoteData | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleQuoteSubmit = (quoteData: QuoteData) => {
    setQuote(quoteData);
    setShowSuccess(true);
    // Hide success message after 3 seconds
    setTimeout(() => setShowSuccess(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Quote Calculator
        </h1>
        <p className="text-gray-600">
          Get an instant quote estimate for your glass service needs
        </p>
      </div>

      {/* Success Message */}
      {showSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-green-700">
            <Check className="w-5 h-5" />
            <span>Quote generated successfully!</span>
          </div>
          <button
            onClick={() => setShowSuccess(false)}
            className="text-green-700 hover:text-green-800"
          >
            <span className="sr-only">Dismiss</span>
            ×
          </button>
        </div>
      )}

      {/* Quote Calculator */}
      <QuoteCalculator
        onSubmit={handleQuoteSubmit}
        className="bg-white rounded-lg shadow-sm border border-gray-200"
      />

      {/* Quote Summary */}
      {quote && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quote Summary</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500">Location</h3>
                <p className="mt-1">{quote.suburb}</p>
                <p className="text-sm text-gray-500">{quote.address}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500">Pricing</h3>
                <p className="mt-1">Base Price: ${quote.basePrice.toFixed(2)}</p>
                <p className="text-sm text-gray-500">
                  Rate Multiplier: {quote.multiplier}x
                </p>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500">Selected Services</h3>
              <ul className="mt-1 list-disc list-inside">
                {quote.services.map(service => (
                  <li key={service}>{service}</li>
                ))}
              </ul>
            </div>

            {quote.notes && (
              <div>
                <h3 className="text-sm font-medium text-gray-500">Additional Notes</h3>
                <p className="mt-1 text-sm text-gray-600">{quote.notes}</p>
              </div>
            )}

            <div className="pt-4 border-t border-gray-200">
              <div className="flex justify-between items-center">
                <span className="text-lg font-medium text-gray-900">Total Estimate</span>
                <span className="text-2xl font-bold text-blue-600">
                  ${quote.adjustedPrice.toFixed(2)}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                All prices are estimates and may vary based on final assessment
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}