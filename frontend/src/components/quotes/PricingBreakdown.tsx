/**
 * Pricing Breakdown Component
 * Displays detailed pricing breakdown for service quotes
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Calculator, DollarSign, TrendingUp, Percent } from 'lucide-react';
import { ServiceQuote } from '@/types';

interface PricingBreakdownProps {
  quote: ServiceQuote;
  className?: string;
}

export const PricingBreakdown: React.FC<PricingBreakdownProps> = ({ quote, className }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(0)}%`;
  };

  const breakdown = quote.pricing_breakdown;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Calculator className="w-5 h-5 text-green-600" />
          Quote Breakdown
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {/* Service Summary */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600 mb-1">Service Type</div>
            <div className="font-medium capitalize">
              {quote.service_type.replace('_', ' ')}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {quote.property_type.charAt(0).toUpperCase() + quote.property_type.slice(1)} • {quote.square_meters}m² • {quote.stories} {quote.stories === 1 ? 'story' : 'stories'}
            </div>
          </div>

          {/* Pricing Details */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Base Rate</span>
              <span className="font-medium">{formatCurrency(breakdown.base_rate)}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Area Cost ({quote.square_meters}m²)</span>
              <span className="font-medium">{formatCurrency(breakdown.area_cost)}</span>
            </div>

            {breakdown.story_multiplier > 1 && (
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-1">
                  <span className="text-sm text-gray-600">Multi-story Adjustment</span>
                  <TrendingUp className="w-3 h-3 text-orange-500" />
                </div>
                <span className="font-medium text-orange-600">
                  +{formatCurrency(breakdown.story_multiplier - breakdown.area_cost)}
                </span>
              </div>
            )}

            {breakdown.difficulty_adjustment !== 0 && (
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-1">
                  <span className="text-sm text-gray-600">Difficulty Adjustment</span>
                  {breakdown.difficulty_adjustment > 0 ? (
                    <TrendingUp className="w-3 h-3 text-red-500" />
                  ) : (
                    <TrendingUp className="w-3 h-3 text-green-500 transform rotate-180" />
                  )}
                </div>
                <span className={`font-medium ${breakdown.difficulty_adjustment > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {breakdown.difficulty_adjustment > 0 ? '+' : ''}{formatCurrency(breakdown.difficulty_adjustment)}
                </span>
              </div>
            )}

            {breakdown.zone_adjustment !== 0 && (
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-1">
                  <span className="text-sm text-gray-600">Location Adjustment ({quote.suburb})</span>
                  <DollarSign className="w-3 h-3 text-blue-500" />
                </div>
                <span className={`font-medium ${breakdown.zone_adjustment > 0 ? 'text-blue-600' : 'text-green-600'}`}>
                  {breakdown.zone_adjustment > 0 ? '+' : ''}{formatCurrency(breakdown.zone_adjustment)}
                </span>
              </div>
            )}

            <div className="border-t pt-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Subtotal</span>
                <span className="font-medium">{formatCurrency(breakdown.total_before_discount)}</span>
              </div>
            </div>

            {breakdown.discount_amount > 0 && (
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-1">
                  <span className="text-sm text-green-600">
                    {quote.frequency === 'one_time' ? 'Promotional' : 'Frequency'} Discount
                  </span>
                  <Percent className="w-3 h-3 text-green-500" />
                </div>
                <span className="font-medium text-green-600">
                  -{formatCurrency(breakdown.discount_amount)}
                </span>
              </div>
            )}

            <div className="border-t-2 pt-3">
              <div className="flex justify-between items-center">
                <span className="text-lg font-semibold">Total Price</span>
                <span className="text-xl font-bold text-green-600">
                  {formatCurrency(breakdown.final_total)}
                </span>
              </div>
            </div>
          </div>

          {/* Additional Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-xs text-blue-800">
              <div className="font-medium mb-1">Quote Details:</div>
              <ul className="space-y-1">
                <li>• Valid until: {new Date(quote.valid_until).toLocaleDateString('en-AU')}</li>
                <li>• Estimated duration: {quote.estimated_duration} hours</li>
                <li>• Service frequency: {quote.frequency.replace('_', ' ')}</li>
                {quote.special_requirements && (
                  <li>• Special requirements included</li>
                )}
              </ul>
            </div>
          </div>

          {/* Frequency Savings Info */}
          {quote.frequency !== 'one_time' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center gap-2 text-green-800">
                <Percent className="w-4 h-4" />
                <span className="font-medium text-sm">Regular Service Savings</span>
              </div>
              <div className="text-xs text-green-700 mt-1">
                You're saving {formatPercentage(breakdown.frequency_discount)} with {quote.frequency.replace('_', ' ')} service!
                {breakdown.discount_amount > 0 && (
                  <> That's {formatCurrency(breakdown.discount_amount)} off your total.</>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
