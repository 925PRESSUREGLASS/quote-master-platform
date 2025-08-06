/**
 * Quote Actions Component
 * Provides actions for managing service quotes (save, email, recalculate, etc.)
 */

import React, { useState } from 'react';
import { 
  Calculator, 
  Save, 
  Mail, 
  Download, 
  Share2, 
  Calendar, 
  Phone,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { ServiceQuote, ServiceQuoteStatus } from '@/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Alert } from '@/components/ui/alert';

interface QuoteActionsProps {
  quote: ServiceQuote | null;
  isCalculating: boolean;
  isValid: boolean;
  onCalculate: () => void;
  onSave: () => Promise<void>;
  onEmail: () => Promise<void>;
  onSchedule?: () => void;
  onShare?: () => void;
}

export const QuoteActions: React.FC<QuoteActionsProps> = ({
  quote,
  isCalculating,
  isValid,
  onCalculate,
  onSave,
  onEmail,
  onSchedule,
  onShare
}) => {
  const [saving, setSaving] = useState(false);
  const [emailing, setEmailing] = useState(false);
  const [saved, setSaved] = useState(false);
  const [emailed, setEmailed] = useState(false);
  const [error, setError] = useState<string>('');

  const handleSave = async () => {
    if (!quote) return;
    
    setSaving(true);
    setError('');
    
    try {
      await onSave();
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError('Failed to save quote. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleEmail = async () => {
    if (!quote) return;
    
    setEmailing(true);
    setError('');
    
    try {
      await onEmail();
      setEmailed(true);
      setTimeout(() => setEmailed(false), 3000);
    } catch (err) {
      setError('Failed to email quote. Please try again.');
    } finally {
      setEmailing(false);
    }
  };

  const handleDownload = () => {
    if (!quote) return;
    
    const quoteData = JSON.stringify(quote, null, 2);
    const blob = new Blob([quoteData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quote-${quote.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getStatusIcon = (status: ServiceQuoteStatus) => {
    switch (status) {
      case ServiceQuoteStatus.DRAFT:
        return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      case ServiceQuoteStatus.PENDING:
        return <Mail className="w-4 h-4 text-blue-600" />;
      case ServiceQuoteStatus.APPROVED:
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case ServiceQuoteStatus.EXPIRED:
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: ServiceQuoteStatus) => {
    switch (status) {
      case ServiceQuoteStatus.DRAFT:
        return 'Draft';
      case ServiceQuoteStatus.PENDING:
        return 'Pending Review';
      case ServiceQuoteStatus.APPROVED:
        return 'Approved by Customer';
      case ServiceQuoteStatus.EXPIRED:
        return 'Expired';
      default:
        return 'Unknown';
    }
  };

  const getStatusColor = (status: ServiceQuoteStatus) => {
    switch (status) {
      case ServiceQuoteStatus.DRAFT:
        return 'bg-yellow-100 text-yellow-800';
      case ServiceQuoteStatus.PENDING:
        return 'bg-blue-100 text-blue-800';
      case ServiceQuoteStatus.APPROVED:
        return 'bg-green-100 text-green-800';
      case ServiceQuoteStatus.EXPIRED:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <Alert>
          <AlertCircle className="w-4 h-4" />
          {error}
        </Alert>
      )}

      {/* Quote Status */}
      {quote && (
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">Quote Status</h4>
            <div className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-2 ${getStatusColor(quote.status)}`}>
              {getStatusIcon(quote.status)}
              {getStatusText(quote.status)}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
            <div>
              <div className="font-medium">Quote ID</div>
              <div className="font-mono text-xs">{quote.id}</div>
            </div>
            <div>
              <div className="font-medium">Total Amount</div>
              <div className="font-semibold text-green-600">
                ${quote.pricing_breakdown.final_total.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="font-medium">Valid Until</div>
              <div>{new Date(quote.valid_until).toLocaleDateString()}</div>
            </div>
            <div>
              <div className="font-medium">Created</div>
              <div>{new Date(quote.created_at).toLocaleDateString()}</div>
            </div>
          </div>
        </Card>
      )}

      {/* Main Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Calculate Quote */}
        <Button
          onClick={onCalculate}
          disabled={!isValid || isCalculating}
          className="flex items-center justify-center gap-2 h-12"
          size="lg"
        >
          {isCalculating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Calculating...
            </>
          ) : (
            <>
              <Calculator className="w-4 h-4" />
              {quote ? 'Recalculate' : 'Calculate Quote'}
            </>
          )}
        </Button>

        {/* Save Quote */}
        <Button
          onClick={handleSave}
          disabled={!quote || saving}
          variant="outline"
          className="flex items-center justify-center gap-2 h-12"
          size="lg"
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : saved ? (
            <>
              <CheckCircle className="w-4 h-4 text-green-600" />
              Saved!
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Quote
            </>
          )}
        </Button>

        {/* Email Quote */}
        <Button
          onClick={handleEmail}
          disabled={!quote || emailing}
          variant="outline"
          className="flex items-center justify-center gap-2 h-12"
          size="lg"
        >
          {emailing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Sending...
            </>
          ) : emailed ? (
            <>
              <CheckCircle className="w-4 h-4 text-green-600" />
              Sent!
            </>
          ) : (
            <>
              <Mail className="w-4 h-4" />
              Email Quote
            </>
          )}
        </Button>
      </div>

      {/* Secondary Actions */}
      {quote && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Button
            onClick={handleDownload}
            variant="outline"
            size="sm"
            className="flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4" />
            Download
          </Button>

          {onShare && (
            <Button
              onClick={onShare}
              variant="outline"
              size="sm"
              className="flex items-center justify-center gap-2"
            >
              <Share2 className="w-4 h-4" />
              Share
            </Button>
          )}

          {onSchedule && quote.status === ServiceQuoteStatus.APPROVED && (
            <Button
              onClick={onSchedule}
              variant="outline"
              size="sm"
              className="flex items-center justify-center gap-2"
            >
              <Calendar className="w-4 h-4" />
              Schedule
            </Button>
          )}

          <Button
            onClick={() => window.open(`tel:${quote.customer_phone}`, '_self')}
            variant="outline"
            size="sm"
            className="flex items-center justify-center gap-2"
          >
            <Phone className="w-4 h-4" />
            Call Customer
          </Button>
        </div>
      )}

      {/* Quote Summary */}
      {quote && (
        <Card className="p-4 bg-gray-50">
          <h5 className="font-medium text-gray-900 mb-3">Quick Summary</h5>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Service:</span>
              <span className="font-medium">{quote.service_type.replace('_', ' ')}</span>
            </div>
            <div className="flex justify-between">
              <span>Location:</span>
              <span className="font-medium">{quote.suburb}, WA</span>
            </div>
            <div className="flex justify-between">
              <span>Property Size:</span>
              <span className="font-medium">{quote.square_meters} m²</span>
            </div>
            <div className="flex justify-between">
              <span>Frequency:</span>
              <span className="font-medium">{quote.frequency.replace('_', ' ')}</span>
            </div>
            <hr className="my-2" />
            <div className="flex justify-between font-semibold text-base">
              <span>Total:</span>
              <span className="text-green-600">${quote.pricing_breakdown.final_total.toFixed(2)}</span>
            </div>
          </div>
        </Card>
      )}

      {/* Help Text */}
      {!quote && (
        <Card className="p-4 border-blue-200 bg-blue-50">
          <div className="flex items-start gap-3">
            <Calculator className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h5 className="font-medium text-blue-900 mb-1">Ready to Calculate</h5>
              <p className="text-sm text-blue-700">
                Once you've filled in all the required information, click "Calculate Quote" to generate 
                your personalized service quote. You'll then be able to save, email, or share the quote.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Next Steps */}
      {quote && quote.status === ServiceQuoteStatus.DRAFT && (
        <Card className="p-4 border-green-200 bg-green-50">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <h5 className="font-medium text-green-900 mb-1">Quote Ready!</h5>
              <p className="text-sm text-green-700 mb-3">
                Your quote has been calculated. Next steps:
              </p>
              <ul className="text-sm text-green-700 space-y-1">
                <li>• Email the quote to the customer</li>
                <li>• Save for your records</li>
                <li>• Schedule a follow-up call</li>
                <li>• Convert to a booking once accepted</li>
              </ul>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
