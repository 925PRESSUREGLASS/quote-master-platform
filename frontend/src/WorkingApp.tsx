import React, { useState } from 'react';
import { PerthSuburbSelector, ServiceTypeSelector } from '@/components/quotes';
import suburbsData from '@/data/perth-suburbs.json';

function WorkingApp() {
  const [selectedSuburb, setSelectedSuburb] = useState('');
  const [address, setAddress] = useState('');
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [basePrice, setBasePrice] = useState(0);

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

      // Update base price
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

    // Simulate API call with enhanced frontend logic
    try {
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

      const mockQuoteResult = {
        quote_id: quoteId,
        suburb: selectedSuburb,
        address,
        services: selectedServices,
        service_names: selectedServiceNames,
        base_price: basePrice,
        adjusted_price: adjustedPrice,
        multiplier: suburbInfo.base_rate_multiplier,
        ai_quote: `Professional ${selectedServiceNames.join(', ')} service for your property in ${selectedSuburb}. Our experienced team will provide quality service with attention to detail, ensuring your glass installations and repairs meet the highest standards.`,
        recommendation: `Based on your location in ${selectedSuburb} (Zone ${suburbInfo.zone}), we recommend scheduling during our standard service hours. The ${suburbInfo.base_rate_multiplier}x rate multiplier applies due to travel distance and service complexity in your area.`,
        estimated_duration: selectedServices.length > 2 ? "4-6 hours for comprehensive service" : "2-4 hours depending on scope of work",
        created_at: new Date().toISOString(),
        status: "draft"
      };

      alert(`🎉 Quote Generated Successfully!\n\n📋 Quote ID: ${mockQuoteResult.quote_id}\n🔧 Services: ${mockQuoteResult.service_names.join(', ')}\n📍 Location: ${mockQuoteResult.suburb} (Zone: ${suburbInfo.zone})\n💰 Total: $${mockQuoteResult.adjusted_price.toFixed(2)}\n⏱️ Duration: ${mockQuoteResult.estimated_duration}\n\n🤖 AI Quote: ${mockQuoteResult.ai_quote}\n\n💡 Recommendation: ${mockQuoteResult.recommendation}`);

      console.log('Enhanced Quote Response:', mockQuoteResult);

    } catch (error) {
      console.error('Error generating quote:', error);
      alert('Failed to generate quote. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Quote Master Pro</h1>
          <p className="mt-2 text-gray-600">Glass & Cleaning Services - Perth, WA</p>
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
            Generate Quote
          </button>
        </form>
      </div>
    </div>
  );
}

export default WorkingApp;
