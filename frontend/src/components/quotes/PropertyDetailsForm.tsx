/**
 * Property Details Form Component
 * Collects property-specific information for accurate quote calculation
 */

import React from 'react';
import { Building, Square, TrendingUp, AlertCircle } from 'lucide-react';
import { PropertyType, ServiceQuoteRequest } from '@/types';

interface PropertyDetailsFormProps {
  propertyType: PropertyType;
  squareMeters: number;
  stories: number;
  difficultyMultiplier: number;
  onChange: (updates: Partial<ServiceQuoteRequest>) => void;
}

export const PropertyDetailsForm: React.FC<PropertyDetailsFormProps> = ({
  propertyType,
  squareMeters,
  stories,
  difficultyMultiplier,
  onChange
}) => {
  const propertyOptions = [
    {
      value: PropertyType.HOUSE,
      label: 'House',
      description: 'Detached house or villa',
      icon: '🏠'
    },
    {
      value: PropertyType.APARTMENT,
      label: 'Apartment/Unit',
      description: 'Apartment, unit, or flat',
      icon: '🏢'
    },
    {
      value: PropertyType.TOWNHOUSE,
      label: 'Townhouse',
      description: 'Townhouse or duplex',
      icon: '🏘️'
    },
    {
      value: PropertyType.COMMERCIAL,
      label: 'Commercial',
      description: 'Office, shop, or commercial building',
      icon: '🏬'
    }
  ];

  const difficultyOptions = [
    {
      value: 0.8,
      label: 'Easy Access',
      description: 'Ground level, easy access, minimal obstacles',
      color: 'text-green-600'
    },
    {
      value: 1.0,
      label: 'Standard',
      description: 'Normal access, some height, typical property',
      color: 'text-blue-600'
    },
    {
      value: 1.2,
      label: 'Moderate Difficulty',
      description: 'Higher windows, some obstacles, steep areas',
      color: 'text-yellow-600'
    },
    {
      value: 1.5,
      label: 'High Difficulty',
      description: 'Very high windows, complex access, safety equipment needed',
      color: 'text-red-600'
    }
  ];

  const getEstimatedSize = (propertyType: PropertyType, stories: number) => {
    const baseSize = {
      [PropertyType.APARTMENT]: { min: 60, max: 120 },
      [PropertyType.TOWNHOUSE]: { min: 100, max: 180 },
      [PropertyType.HOUSE]: { min: 120, max: 300 },
      [PropertyType.COMMERCIAL]: { min: 200, max: 1000 }
    };

    const base = baseSize[propertyType];
    const multiplier = stories > 1 ? 1 + (stories - 1) * 0.6 : 1;
    
    return {
      min: Math.round(base.min * multiplier),
      max: Math.round(base.max * multiplier)
    };
  };

  const estimatedSize = getEstimatedSize(propertyType, stories);
  const isCustomSize = squareMeters < estimatedSize.min * 0.8 || squareMeters > estimatedSize.max * 1.2;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Building className="w-5 h-5 text-blue-600" />
          Property Details
        </h3>

        {/* Property Type Selection */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Property Type
            </label>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {propertyOptions.map((option) => (
                <div
                  key={option.value}
                  className={`relative border rounded-lg p-3 cursor-pointer transition-all ${
                    propertyType === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => onChange({ property_type: option.value })}
                >
                  <div className="text-center">
                    <div className="text-2xl mb-2">{option.icon}</div>
                    <h4 className="font-medium text-sm">{option.label}</h4>
                    <p className="text-xs text-gray-600 mt-1">{option.description}</p>
                  </div>
                  {propertyType === option.value && (
                    <div className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full"></div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Property Size */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Square className="w-4 h-4 inline mr-1" />
            Property Size (square meters)
          </label>
          <input
            type="number"
            min="10"
            max="2000"
            value={squareMeters}
            onChange={(e) => onChange({ square_meters: parseInt(e.target.value) || 0 })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter size in m²"
          />
          <div className="mt-2 text-xs text-gray-500">
            Estimated for {propertyType}: {estimatedSize.min} - {estimatedSize.max} m²
          </div>
          {isCustomSize && (
            <div className="mt-1 flex items-center gap-1 text-xs text-amber-600">
              <AlertCircle className="w-3 h-3" />
              Custom size - please verify measurement accuracy
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <TrendingUp className="w-4 h-4 inline mr-1" />
            Number of Stories
          </label>
          <select
            value={stories}
            onChange={(e) => onChange({ stories: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={1}>1 Story</option>
            <option value={2}>2 Stories</option>
            <option value={3}>3 Stories</option>
            <option value={4}>4+ Stories</option>
          </select>
          <div className="mt-2 text-xs text-gray-500">
            {stories > 1 && `Multi-story properties may require additional safety equipment`}
          </div>
        </div>
      </div>

      {/* Difficulty Assessment */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Access Difficulty
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {difficultyOptions.map((option) => (
            <div
              key={option.value}
              className={`relative border rounded-lg p-3 cursor-pointer transition-all ${
                difficultyMultiplier === option.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => onChange({ difficulty_multiplier: option.value })}
            >
              <div className="flex items-center justify-between mb-1">
                <h4 className={`font-medium text-sm ${option.color}`}>{option.label}</h4>
                {difficultyMultiplier === option.value && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                )}
              </div>
              <p className="text-xs text-gray-600">{option.description}</p>
              <div className="mt-2 text-xs text-gray-500">
                Price multiplier: {option.value}x
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Property Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h5 className="font-medium text-gray-900 mb-2">Property Summary</h5>
        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Type:</span> {propertyOptions.find(p => p.value === propertyType)?.label}
          </div>
          <div>
            <span className="font-medium">Size:</span> {squareMeters} m²
          </div>
          <div>
            <span className="font-medium">Stories:</span> {stories}
          </div>
          <div>
            <span className="font-medium">Difficulty:</span> {difficultyOptions.find(d => d.value === difficultyMultiplier)?.label}
          </div>
        </div>
        
        {(stories > 2 || difficultyMultiplier > 1.2) && (
          <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
            <AlertCircle className="w-3 h-3 inline mr-1" />
            <strong>Note:</strong> This property may require specialized equipment or additional safety measures, 
            which could affect final pricing and scheduling.
          </div>
        )}
      </div>
    </div>
  );
};
