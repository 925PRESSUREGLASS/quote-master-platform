/**
 * Service Selection Form Component
 * Allows users to select service type, frequency, and special requirements
 */

import React from 'react';
import { Wrench, Calendar, FileText } from 'lucide-react';
import { ServiceType, ServiceFrequency, ServiceQuoteRequest } from '@/types';

interface ServiceSelectionFormProps {
  serviceType: ServiceType;
  frequency: ServiceFrequency;
  specialRequirements?: string;
  onChange: (updates: Partial<ServiceQuoteRequest>) => void;
}

export const ServiceSelectionForm: React.FC<ServiceSelectionFormProps> = ({
  serviceType,
  frequency,
  specialRequirements,
  onChange
}) => {
  const serviceOptions = [
    {
      value: ServiceType.WINDOW_CLEANING,
      label: 'Window Cleaning',
      description: 'Professional window cleaning for residential and commercial properties',
      icon: '🪟'
    },
    {
      value: ServiceType.PRESSURE_CLEANING,
      label: 'Pressure Cleaning',
      description: 'High-pressure cleaning for driveways, patios, and building exteriors',
      icon: '💧'
    },
    {
      value: ServiceType.BOTH,
      label: 'Combined Service',
      description: 'Window cleaning and pressure cleaning package (save 10%)',
      icon: '🏠'
    }
  ];

  const frequencyOptions = [
    {
      value: ServiceFrequency.ONE_TIME,
      label: 'One-time Service',
      description: 'Single service visit',
      discount: 0
    },
    {
      value: ServiceFrequency.WEEKLY,
      label: 'Weekly',
      description: 'Every week',
      discount: 15
    },
    {
      value: ServiceFrequency.FORTNIGHTLY,
      label: 'Fortnightly',
      description: 'Every 2 weeks',
      discount: 10
    },
    {
      value: ServiceFrequency.MONTHLY,
      label: 'Monthly',
      description: 'Once per month',
      discount: 8
    },
    {
      value: ServiceFrequency.QUARTERLY,
      label: 'Quarterly',
      description: 'Every 3 months',
      discount: 5
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Wrench className="w-5 h-5 text-blue-600" />
          Service Selection
        </h3>

        {/* Service Type Selection */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              What service do you need?
            </label>
            <div className="grid gap-3">
              {serviceOptions.map((option) => (
                <div
                  key={option.value}
                  className={`relative border rounded-lg p-4 cursor-pointer transition-all ${
                    serviceType === option.value
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => onChange({ service_type: option.value })}
                >
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">{option.icon}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900">{option.label}</h4>
                        {serviceType === option.value && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{option.description}</p>
                      {option.value === ServiceType.BOTH && (
                        <div className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 mt-2">
                          Save 10%
                        </div>
                      )}
                    </div>
                  </div>
                  <input
                    type="radio"
                    name="serviceType"
                    value={option.value}
                    checked={serviceType === option.value}
                    onChange={() => onChange({ service_type: option.value })}
                    className="absolute top-4 right-4"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-md font-medium mb-3 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-blue-600" />
          Service Frequency
        </h4>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {frequencyOptions.map((option) => (
            <div
              key={option.value}
              className={`relative border rounded-lg p-3 cursor-pointer transition-all ${
                frequency === option.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => onChange({ frequency: option.value })}
            >
              <div className="flex items-center justify-between mb-1">
                <h5 className="font-medium text-sm">{option.label}</h5>
                {frequency === option.value && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                )}
              </div>
              <p className="text-xs text-gray-600 mb-2">{option.description}</p>
              {option.discount > 0 && (
                <div className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                  Save {option.discount}%
                </div>
              )}
              <input
                type="radio"
                name="frequency"
                value={option.value}
                checked={frequency === option.value}
                onChange={() => onChange({ frequency: option.value })}
                className="sr-only"
              />
            </div>
          ))}
        </div>
      </div>

      <div>
        <h4 className="text-md font-medium mb-3 flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-600" />
          Special Requirements (Optional)
        </h4>
        
        <textarea
          value={specialRequirements || ''}
          onChange={(e) => onChange({ special_requirements: e.target.value })}
          placeholder="Any special requirements, access instructions, or additional details..."
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical"
        />
        <p className="text-xs text-gray-500 mt-1">
          Example: "High windows require ladder access", "Please use back gate", "Fragile plants near windows"
        </p>
      </div>

      {/* Service Info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h5 className="font-medium text-gray-900 mb-2">What's Included</h5>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-gray-600">
          {serviceType === ServiceType.WINDOW_CLEANING && (
            <div>
              <strong>Window Cleaning:</strong>
              <ul className="mt-1 space-y-1 text-xs">
                <li>• Interior and exterior cleaning</li>
                <li>• Frame and sill cleaning</li>
                <li>• Screen cleaning (if requested)</li>
                <li>• Professional squeegee finish</li>
              </ul>
            </div>
          )}
          
          {serviceType === ServiceType.PRESSURE_CLEANING && (
            <div>
              <strong>Pressure Cleaning:</strong>
              <ul className="mt-1 space-y-1 text-xs">
                <li>• Driveways and walkways</li>
                <li>• Patios and outdoor areas</li>
                <li>• Building exterior walls</li>
                <li>• Gutter and downpipe cleaning</li>
              </ul>
            </div>
          )}
          
          {serviceType === ServiceType.BOTH && (
            <>
              <div>
                <strong>Window Cleaning:</strong>
                <ul className="mt-1 space-y-1 text-xs">
                  <li>• Interior and exterior cleaning</li>
                  <li>• Frame and sill cleaning</li>
                  <li>• Screen cleaning (if requested)</li>
                </ul>
              </div>
              <div>
                <strong>Pressure Cleaning:</strong>
                <ul className="mt-1 space-y-1 text-xs">
                  <li>• Driveways and walkways</li>
                  <li>• Patios and outdoor areas</li>
                  <li>• Building exterior walls</li>
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
