/**
 * Perth Suburb Selector Component
 * Provides searchable dropdown for Perth suburbs with pricing zones
 */

import React, { useState, useEffect } from 'react';
import { MapPin, Search, DollarSign } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface SuburbInfo {
  name: string;
  zone: string;
  base_rate_multiplier: number;
  postcode: string;
  region: string;
}

interface PerthSuburbSelectorProps {
  selectedSuburb: string;
  address: string;
  suburbs: SuburbInfo[];
  onChange: (suburb: string, address: string) => void;
  className?: string;
}

export const PerthSuburbSelector: React.FC<PerthSuburbSelectorProps> = ({
  selectedSuburb,
  address,
  suburbs,
  onChange,
  className
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredSuburbs, setFilteredSuburbs] = useState<SuburbInfo[]>(suburbs);

  useEffect(() => {
    const filtered = suburbs.filter(suburb =>
      suburb.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      suburb.postcode.includes(searchTerm) ||
      suburb.region.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredSuburbs(filtered);
  }, [searchTerm, suburbs]);

  const selectedSuburbInfo = suburbs.find(s => s.name === selectedSuburb);

  const handleSuburbSelect = (suburb: SuburbInfo) => {
    onChange(suburb.name, address);
    setIsOpen(false);
    setSearchTerm('');
  };

  const getPriceIndicator = (multiplier: number) => {
    if (multiplier <= 1.0) return { label: 'Standard', color: 'text-green-600' };
    if (multiplier <= 1.2) return { label: 'Moderate', color: 'text-yellow-600' };
    return { label: 'Premium', color: 'text-red-600' };
  };

  return (
    <div className={cn("space-y-6", className)}>
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-blue-600" />
          Location Details
        </h3>
        
        {/* Address Input */}
        <div className="space-y-4">
          <div>
            <label
              htmlFor="property-address"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Property Address
            </label>
            <input
              id="property-address"
              name="address"
              type="text"
              value={address}
              onChange={(e) => onChange(selectedSuburb, e.target.value)}
              placeholder="Enter your full property address"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              Include street number, street name, and postcode
            </p>
          </div>

          {/* Suburb Selector */}
            <div className="relative">
              <label
                htmlFor="suburb-selector"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Perth Suburb
              </label>

              <div className="relative">
                <button
                  id="suburb-selector"
                  type="button"
                  aria-haspopup="true"
                  aria-expanded={isOpen}
                  aria-controls="suburb-options"
                  onClick={() => setIsOpen(!isOpen)}
                  className="w-full px-3 py-2 text-left border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white flex items-center justify-between"
                >
                  <span className={selectedSuburb ? 'text-gray-900' : 'text-gray-500'}>
                    {selectedSuburb || 'Select a suburb...'}
                  </span>
                <svg
                  className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isOpen && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
                  {/* Search Input */}
                  <div className="p-3 border-b border-gray-200">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <input
                          id="suburb-search"
                          type="text"
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          placeholder="Search suburbs..."
                          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                          autoFocus
                          aria-label="Search suburbs"
                        />
                      </div>
                    </div>

                  {/* Suburbs List */}
                  <div
                    id="suburb-options"
                    role="listbox"
                    className="max-h-60 overflow-y-auto"
                  >
                    {filteredSuburbs.length > 0 ? (
                      filteredSuburbs.map((suburb) => {
                        const priceInfo = getPriceIndicator(suburb.base_rate_multiplier);
                        return (
                          <button
                            key={suburb.name}
                            type="button"
                            role="option"
                            aria-selected={selectedSuburb === suburb.name}
                            onClick={() => handleSuburbSelect(suburb)}
                            className="w-full px-3 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none flex items-center justify-between"
                          >
                            <div>
                              <div className="font-medium text-gray-900">{suburb.name}</div>
                              <div className="text-sm text-gray-500">{suburb.postcode} - {suburb.region}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              <DollarSign className={`w-4 h-4 ${priceInfo.color}`} />
                              <span className={`text-xs font-medium ${priceInfo.color}`}>
                                {priceInfo.label}
                              </span>
                              <span className="text-xs text-gray-400">
                                {suburb.base_rate_multiplier}x
                              </span>
                            </div>
                          </button>
                        );
                      })
                    ) : (
                      <div className="px-3 py-3 text-center text-gray-500">
                        No suburbs found matching "{searchTerm}"
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Selected Suburb Info */}
      {selectedSuburbInfo && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-blue-900">{selectedSuburbInfo.name}</h4>
              <p className="text-sm text-blue-700">Pricing Zone {selectedSuburbInfo.zone}</p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-1 text-blue-600">
                <DollarSign className="w-4 h-4" />
                <span className="font-medium">
                  {getPriceIndicator(selectedSuburbInfo.base_rate_multiplier).label}
                </span>
              </div>
              <p className="text-xs text-blue-600">
                {selectedSuburbInfo.base_rate_multiplier}x base rate
              </p>
            </div>
          </div>
          
          <div className="mt-3 text-xs text-blue-700">
            <p>
              <strong>Zone Information:</strong> This suburb is in pricing zone {selectedSuburbInfo.zone}. 
              {selectedSuburbInfo.base_rate_multiplier > 1 
                ? ` Additional charges apply due to travel distance and service complexity.`
                : ` Standard rates apply for this central location.`
              }
            </p>
          </div>
        </div>
      )}

      {/* Zone Legend */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Perth Pricing Zones</h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <DollarSign className="w-3 h-3 text-green-600" />
            <span className="text-green-600 font-medium">Standard</span>
            <span className="text-gray-500">(1.0x rate)</span>
          </div>
          <div className="flex items-center gap-2">
            <DollarSign className="w-3 h-3 text-yellow-600" />
            <span className="text-yellow-600 font-medium">Moderate</span>
            <span className="text-gray-500">(1.0-1.2x rate)</span>
          </div>
          <div className="flex items-center gap-2">
            <DollarSign className="w-3 h-3 text-red-600" />
            <span className="text-red-600 font-medium">Premium</span>
            <span className="text-gray-500">(1.2x+ rate)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
