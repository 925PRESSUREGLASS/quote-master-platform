/**
 * Customer Details Form Component
 * Collects customer information and preferences for quote delivery and communication
 */

import React, { useState } from 'react';
import { User, Phone, Mail, Calendar, MessageSquare, Bell } from 'lucide-react';
import { ServiceQuoteRequest } from '@/types';
import { Card } from '@/components/ui/card';

interface CustomerDetailsFormProps {
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  preferredContactTime?: string;
  notes?: string;
  onChange: (updates: Partial<ServiceQuoteRequest>) => void;
}

export const CustomerDetailsForm: React.FC<CustomerDetailsFormProps> = ({
  customerName,
  customerEmail,
  customerPhone,
  preferredContactTime,
  notes,
  onChange
}) => {
  const [emailValid, setEmailValid] = useState<boolean>(true);
  const [phoneValid, setPhoneValid] = useState<boolean>(true);

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePhone = (phone: string) => {
    // Australian phone number validation (mobile and landline)
    const phoneRegex = /^(?:\+?61|0)[2-9]\d{8}$/;
    const cleaned = phone.replace(/[\s\-\(\)]/g, '');
    return phoneRegex.test(cleaned);
  };

  const formatPhone = (phone: string) => {
    const cleaned = phone.replace(/\D/g, '');
    
    // Handle different Australian formats
    if (cleaned.length >= 10) {
      if (cleaned.startsWith('61')) {
        // International format
        return `+${cleaned.slice(0, 2)} ${cleaned.slice(2, 3)} ${cleaned.slice(3, 7)} ${cleaned.slice(7)}`;
      } else if (cleaned.startsWith('0')) {
        // Local format
        return `${cleaned.slice(0, 2)} ${cleaned.slice(2, 6)} ${cleaned.slice(6)}`;
      }
    }
    return phone;
  };

  const handleEmailChange = (email: string) => {
    onChange({ customer_email: email });
    setEmailValid(email === '' || validateEmail(email));
  };

  const handlePhoneChange = (phone: string) => {
    const formatted = formatPhone(phone);
    onChange({ customer_phone: formatted });
    setPhoneValid(phone === '' || validatePhone(phone));
  };

  const timeSlots = [
    { value: 'morning', label: '9:00 AM - 12:00 PM', description: 'Morning (best for residential)' },
    { value: 'afternoon', label: '12:00 PM - 5:00 PM', description: 'Afternoon (standard hours)' },
    { value: 'evening', label: '5:00 PM - 7:00 PM', description: 'Early evening (after work)' },
    { value: 'flexible', label: 'Flexible', description: 'Any time during business hours' }
  ];

  const isFormValid = () => {
    return customerName.trim() !== '' && 
           emailValid && 
           customerEmail.trim() !== '' && 
           phoneValid && 
           customerPhone.trim() !== '';
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <User className="w-5 h-5 text-blue-600" />
          Contact Information
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Customer Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="w-4 h-4 inline mr-1" />
              Full Name *
            </label>
            <input
              type="text"
              value={customerName}
              onChange={(e) => onChange({ customer_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your full name"
              required
            />
          </div>

          {/* Customer Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Mail className="w-4 h-4 inline mr-1" />
              Email Address *
            </label>
            <input
              type="email"
              value={customerEmail}
              onChange={(e) => handleEmailChange(e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                !emailValid ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="your.email@example.com"
              required
            />
            {!emailValid && customerEmail && (
              <p className="mt-1 text-xs text-red-600">Please enter a valid email address</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {/* Customer Phone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Phone className="w-4 h-4 inline mr-1" />
              Phone Number *
            </label>
            <input
              type="tel"
              value={customerPhone}
              onChange={(e) => handlePhoneChange(e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                !phoneValid ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="04XX XXX XXX or 08 XXXX XXXX"
              required
            />
            {!phoneValid && customerPhone && (
              <p className="mt-1 text-xs text-red-600">Please enter a valid Australian phone number</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Mobile: 04XX XXX XXX | Landline: 0X XXXX XXXX
            </p>
          </div>

          {/* Preferred Contact Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar className="w-4 h-4 inline mr-1" />
              Preferred Contact Time
            </label>
            <select
              value={preferredContactTime || ''}
              onChange={(e) => onChange({ preferred_contact_time: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select preferred time</option>
              {timeSlots.map((slot) => (
                <option key={slot.value} value={slot.value}>
                  {slot.label}
                </option>
              ))}
            </select>
            {preferredContactTime && (
              <p className="mt-1 text-xs text-gray-500">
                {timeSlots.find(s => s.value === preferredContactTime)?.description}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Communication Preferences */}
      <Card className="p-4">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <Bell className="w-4 h-4 text-blue-600" />
          Communication Preferences
        </h4>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4" />
            <span>Quote will be emailed to: <strong>{customerEmail || 'your email'}</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4" />
            <span>We'll call: <strong>{customerPhone || 'your phone'}</strong></span>
            {preferredContactTime && (
              <span className="text-blue-600">
                ({timeSlots.find(s => s.value === preferredContactTime)?.label})
              </span>
            )}
          </div>
          <div className="mt-3 p-2 bg-blue-50 text-blue-700 rounded text-xs">
            We respect your privacy. Your information is only used for quote delivery and service scheduling.
          </div>
        </div>
      </Card>

      {/* Additional Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <MessageSquare className="w-4 h-4 inline mr-1" />
          Additional Notes or Special Requirements
        </label>
        <textarea
          value={notes || ''}
          onChange={(e) => onChange({ notes: e.target.value })}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical"
          placeholder="Any special requirements, access instructions, or additional information that might help us provide a more accurate quote..."
        />
        <div className="mt-1 flex justify-between text-xs text-gray-500">
          <span>Optional - helps us provide better service</span>
          <span>{(notes || '').length}/500</span>
        </div>
      </div>

      {/* Form Validation Status */}
      {!isFormValid() && (
        <Card className="p-4 border-yellow-200 bg-yellow-50">
          <div className="flex items-center gap-2 text-yellow-800">
            <Bell className="w-4 h-4" />
            <strong>Required Information</strong>
          </div>
          <ul className="mt-2 text-sm text-yellow-700 space-y-1">
            {!customerName.trim() && <li>• Full name is required</li>}
            {!customerEmail.trim() && <li>• Email address is required</li>}
            {!emailValid && customerEmail && <li>• Valid email address is required</li>}
            {!customerPhone.trim() && <li>• Phone number is required</li>}
            {!phoneValid && customerPhone && <li>• Valid Australian phone number is required</li>}
          </ul>
        </Card>
      )}

      {/* Contact Summary */}
      {isFormValid() && (
        <Card className="p-4 bg-green-50 border-green-200">
          <div className="flex items-center gap-2 text-green-800 mb-2">
            <User className="w-4 h-4" />
            <strong>Contact Summary</strong>
          </div>
          <div className="text-sm text-green-700 space-y-1">
            <div><strong>Customer:</strong> {customerName}</div>
            <div><strong>Email:</strong> {customerEmail}</div>
            <div><strong>Phone:</strong> {customerPhone}</div>
            {preferredContactTime && (
              <div>
                <strong>Best time to call:</strong> {timeSlots.find(s => s.value === preferredContactTime)?.label}
              </div>
            )}
            {notes && (
              <div className="mt-2">
                <strong>Notes:</strong> {notes.substring(0, 100)}{notes.length > 100 ? '...' : ''}
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
