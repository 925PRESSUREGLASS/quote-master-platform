/**
 * Service Quote Calculator - Main Component
 * Professional window/pressure cleaning quote calculator for Perth, WA
 */

import React, { useState, useEffect } from 'react';
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
// import { Button } from '@/components/ui/button';
// import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Calculator, MapPin, Building, Wrench } from 'lucide-react';
import { CustomerDetailsForm } from './CustomerDetailsForm';
import { ServiceSelectionForm } from './ServiceSelectionForm';
import { PropertyDetailsForm } from './PropertyDetailsForm';
import { PerthSuburbSelector, SuburbInfo } from './PerthSuburbSelector';
import { PricingBreakdown } from './PricingBreakdown';
import { QuoteActions } from './QuoteActions';
import { quoteService } from '@/services/quotes';
import suburbsData from '@/data/perth-suburbs.json';
import {
  ServiceQuoteRequest,
  ServiceQuoteCalculation,
  ServiceQuote,
  ServiceType,
  PropertyType,
  ServiceFrequency,
  ContactPreference
} from '@/types';

interface ServiceQuoteCalculatorProps {
  onQuoteCreated?: (quote: ServiceQuote) => void;
  initialData?: Partial<ServiceQuoteRequest>;
  mode?: 'calculator' | 'full-form';
}

export const ServiceQuoteCalculator: React.FC<ServiceQuoteCalculatorProps> = ({
  onQuoteCreated,
  initialData,
  mode = 'full-form'
}) => {
  // Form state
  const [formData, setFormData] = useState<ServiceQuoteRequest>({
    customer_name: initialData?.customer_name || '',
    customer_email: initialData?.customer_email || '',
    customer_phone: initialData?.customer_phone || '',
    customer_address: initialData?.customer_address || '',
    suburb: initialData?.suburb || '',
    service_type: initialData?.service_type || ServiceType.WINDOW_CLEANING,
    property_type: initialData?.property_type || PropertyType.HOUSE,
    square_meters: initialData?.square_meters || 100,
    stories: initialData?.stories || 1,
    difficulty_multiplier: initialData?.difficulty_multiplier || 1.0,
    frequency: initialData?.frequency || ServiceFrequency.ONE_TIME,
    contact_preference: initialData?.contact_preference || ContactPreference.EMAIL,
    special_requirements: initialData?.special_requirements || '',
    notes: initialData?.notes || '',
    preferred_contact_time: initialData?.preferred_contact_time || ''
  });

  // State management
  const [currentStep, setCurrentStep] = useState(1);
  const [isCalculating, setIsCalculating] = useState(false);
  const [isCreatingQuote, setIsCreatingQuote] = useState(false);
  const [calculatedQuote, setCalculatedQuote] = useState<ServiceQuote | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [suburbs] = useState<SuburbInfo[]>(suburbsData.suburbs);

  // Initialize with default data if needed
  useEffect(() => {
    if (initialData) {
      setFormData(prev => ({ ...prev, ...initialData }));
    }
  }, [initialData]);

  // Auto-calculate quote when key fields change
  useEffect(() => {
    if (formData.suburb && formData.square_meters > 0 && mode === 'calculator') {
      handleCalculateQuote();
    }
  }, [
    formData.service_type,
    formData.property_type,
    formData.square_meters,
    formData.stories,
    formData.suburb,
    formData.frequency,
    formData.difficulty_multiplier
  ]);

  const handleCalculateQuote = async () => {
    if (!formData.suburb || formData.square_meters <= 0) {
      setError('Please fill in suburb and property size to calculate quote');
      return;
    }

    setIsCalculating(true);
    setError(null);

    try {
      const calculationData: ServiceQuoteCalculation = {
        service_type: formData.service_type,
        property_type: formData.property_type,
        square_meters: formData.square_meters,
        stories: formData.stories,
        suburb: formData.suburb,
        frequency: formData.frequency,
        difficulty_multiplier: formData.difficulty_multiplier
      };

      const quote = await quoteService.calculateServiceQuote(calculationData);
      setCalculatedQuote(quote);
    } catch (error: any) {
      console.error('Failed to calculate quote:', error);
      setError(error.response?.data?.detail || 'Failed to calculate quote. Please try again.');
    } finally {
      setIsCalculating(false);
    }
  };

  const handleCreateQuote = async () => {
    if (!calculatedQuote) {
      await handleCalculateQuote();
      if (!calculatedQuote) return;
    }

    // Validate required fields
    if (!formData.customer_name || !formData.customer_email) {
      setError('Please fill in customer name and email to create quote');
      return;
    }

    setIsCreatingQuote(true);
    setError(null);

    try {
      const createdQuote = await quoteService.createServiceQuote(formData);
      onQuoteCreated?.(createdQuote);

      // Reset form or show success message
      setCalculatedQuote(null);
      setCurrentStep(1);
    } catch (error: any) {
      console.error('Failed to create quote:', error);
      setError(error.response?.data?.detail || 'Failed to create quote. Please try again.');
    } finally {
      setIsCreatingQuote(false);
    }
  };

  const updateFormData = (updates: Partial<ServiceQuoteRequest>) => {
    setFormData(prev => ({ ...prev, ...updates }));
  };

  const nextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const renderStepIndicator = () => {
    const steps = [
      { number: 1, title: 'Service Details', icon: Wrench },
      { number: 2, title: 'Property Details', icon: Building },
      { number: 3, title: 'Location', icon: MapPin },
      { number: 4, title: 'Customer Info', icon: Calculator }
    ];

    return (
      <div className="flex items-center justify-between mb-8">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = currentStep === step.number;
          const isCompleted = currentStep > step.number;

          return (
            <React.Fragment key={step.number}>
              <div className="flex flex-col items-center">
                <div className={`
                  w-12 h-12 rounded-full flex items-center justify-center border-2 transition-colors
                  ${isActive ? 'bg-blue-600 border-blue-600 text-white' :
                    isCompleted ? 'bg-green-600 border-green-600 text-white' :
                    'bg-gray-100 border-gray-300 text-gray-500'}
                `}>
                  <Icon className="w-5 h-5" />
                </div>
                <span className={`mt-2 text-sm font-medium ${
                  isActive ? 'text-blue-600' :
                  isCompleted ? 'text-green-600' :
                  'text-gray-500'
                }`}>
                  {step.title}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div className={`flex-1 h-0.5 mx-4 ${
                  isCompleted ? 'bg-green-600' : 'bg-gray-300'
                }`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <ServiceSelectionForm
            serviceType={formData.service_type}
            frequency={formData.frequency}
            specialRequirements={formData.special_requirements}
            onChange={updateFormData}
          />
        );
      case 2:
        return (
          <PropertyDetailsForm
            propertyType={formData.property_type}
            squareMeters={formData.square_meters}
            stories={formData.stories}
            difficultyMultiplier={formData.difficulty_multiplier}
            onChange={updateFormData}
          />
        );
      case 3:
        return (
          <PerthSuburbSelector
            selectedSuburb={formData.suburb}
            address={formData.customer_address}
            suburbs={suburbs}
            onChange={(suburb, address) => updateFormData({ suburb, customer_address: address })}
          />
        );
      case 4:
        return (
          <CustomerDetailsForm
            customerName={formData.customer_name}
            customerEmail={formData.customer_email}
            customerPhone={formData.customer_phone}
            contactPreference={formData.contact_preference}
            preferredContactTime={formData.preferred_contact_time}
            notes={formData.notes}
            onChange={updateFormData}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="w-6 h-6 text-blue-600" />
            Service Quote Calculator
          </CardTitle>
          <CardDescription>
            Get an instant quote for professional window and pressure cleaning services in Perth, WA
          </CardDescription>
        </CardHeader>

        <CardContent>
          {error && (
            <Alert className="mb-6 border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {mode === 'full-form' && renderStepIndicator()}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Form Section */}
            <div className="lg:col-span-2">
              {renderStepContent()}

              {/* Navigation Buttons */}
              {mode === 'full-form' && (
                <div className="flex justify-between mt-8">
                  <Button
                    variant="outline"
                    onClick={prevStep}
                    disabled={currentStep === 1}
                  >
                    Previous
                  </Button>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={handleCalculateQuote}
                      disabled={isCalculating || !formData.suburb || formData.square_meters <= 0}
                    >
                      {isCalculating ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Calculating...
                        </>
                      ) : (
                        'Calculate Quote'
                      )}
                    </Button>

                    {currentStep < 4 ? (
                      <Button onClick={nextStep}>
                        Next
                      </Button>
                    ) : (
                      <Button
                        onClick={handleCreateQuote}
                        disabled={isCreatingQuote || !calculatedQuote}
                      >
                        {isCreatingQuote ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Creating Quote...
                          </>
                        ) : (
                          'Create Quote'
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Pricing Section */}
            <div className="lg:col-span-1">
              {calculatedQuote ? (
                <>
                  <PricingBreakdown quote={calculatedQuote} />
                  <QuoteActions
                    quote={calculatedQuote}
                    onRecalculate={handleCalculateQuote}
                    className="mt-4"
                  />
                </>
              ) : (
                <Card className="p-6 text-center text-gray-500">
                  <Calculator className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p>Fill in the details to see your quote</p>
                </Card>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
