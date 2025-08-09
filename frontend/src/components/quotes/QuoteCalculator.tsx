import React, { useState } from 'react';
import { Calculator, DollarSign } from 'lucide-react';
import { PerthSuburbSelector } from './PerthSuburbSelector';
import { ServiceTypeSelector, ServiceOption } from './ServiceTypeSelector';
import suburbs from '@/data/perth-suburbs.json';

interface QuoteCalculatorProps {
  className?: string;
  onSubmit: (quoteData: QuoteData) => void;
}

export interface QuoteData {
  suburb: string;
  address: string;
  basePrice: number;
  adjustedPrice: number;
  multiplier: number;
  services: string[];
  notes: string;
}

export const QuoteCalculator: React.FC<QuoteCalculatorProps> = ({
  className,
  onSubmit
}) => {
  const [selectedSuburb, setSelectedSuburb] = useState('');
  const [address, setAddress] = useState('');
  const [basePrice, setBasePrice] = useState(0);
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [notes, setNotes] = useState('');

  const handleLocationChange = (suburb: string, address: string) => {
    setSelectedSuburb(suburb);
    setAddress(address);
  };

  const calculateAdjustedPrice = () => {
    const suburbInfo = suburbs.suburbs.find(s => s.name === selectedSuburb);
    if (!suburbInfo) return basePrice;
    return basePrice * suburbInfo.base_rate_multiplier;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const suburbInfo = suburbs.suburbs.find(s => s.name === selectedSuburb);
    if (!suburbInfo) return;

    const quoteData: QuoteData = {
      suburb: selectedSuburb,
      address,
      basePrice,
      adjustedPrice: calculateAdjustedPrice(),
      multiplier: suburbInfo.base_rate_multiplier,
      services: selectedServices,
      notes
    };

    onSubmit(quoteData);
  };

  const services: ServiceOption[] = [
    { id: 'residential', name: 'Residential Glass', basePrice: 150 },
    { id: 'commercial', name: 'Commercial Glazing', basePrice: 250 },
    { id: 'emergency', name: 'Emergency Service', basePrice: 350 },
    { id: 'shower', name: 'Shower Screens', basePrice: 200 },
    { id: 'mirrors', name: 'Mirrors', basePrice: 180 },
    { id: 'windows', name: 'Window Repairs', basePrice: 160 }
  ];

  const handleServiceChange = (servicesSelected: string[], price: number) => {
    setSelectedServices(servicesSelected);
    setBasePrice(price);
  };

  return (
    <form onSubmit={handleSubmit} className={className}>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Calculator className="w-6 h-6 text-blue-600" />
            Quote Calculator
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Select your location and services to get an instant quote estimate.
          </p>
        </div>

        {/* Location Section */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Location Details</h3>
          <PerthSuburbSelector
            selectedSuburb={selectedSuburb}
            address={address}
            suburbs={suburbs.suburbs}
            onChange={handleLocationChange}
          />
        </div>

        {/* Services Section */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Services</h3>
          <ServiceTypeSelector services={services} onChange={handleServiceChange} />
        </div>

        {/* Additional Notes */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Notes</h3>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={4}
            placeholder="Add any special requirements or notes..."
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
                    ? `${(suburbs.suburbs.find(s => s.name === selectedSuburb)?.base_rate_multiplier || 1).toFixed(2)}x`
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
          <DollarSign className="w-5 h-5" />
          Generate Quote
        </button>
      </div>
    </form>
  );
};
