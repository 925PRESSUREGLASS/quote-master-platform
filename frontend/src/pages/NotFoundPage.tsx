import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft, Search } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          {/* 404 Illustration */}
          <div className="mx-auto h-48 w-48 mb-8">
            <div className="text-9xl font-bold text-gray-300">404</div>
          </div>

          {/* Error Message */}
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Page Not Found
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            The page you're looking for doesn't exist or has been moved.
          </p>

          {/* Action Buttons */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/" className="btn btn-primary">
                <Home className="w-4 h-4 mr-2" />
                Go Home
              </Link>
              <button 
                onClick={() => window.history.back()} 
                className="btn btn-outline"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Go Back
              </button>
            </div>

            {/* Search Suggestion */}
            <div className="mt-8">
              <p className="text-sm text-gray-500 mb-4">
                Try searching for what you need:
              </p>
              <div className="relative max-w-sm mx-auto">
                <input
                  type="text"
                  placeholder="Search quotes, features..."
                  className="input pl-10"
                />
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div className="mt-12">
            <h3 className="text-sm font-medium text-gray-900 mb-4">
              Popular Pages
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <Link 
                to="/app/quotes/generate" 
                className="text-primary-600 hover:text-primary-500"
              >
                Generate Quotes
              </Link>
              <Link 
                to="/app/voice/record" 
                className="text-primary-600 hover:text-primary-500"
              >
                Voice Recording
              </Link>
              <Link 
                to="/app/quotes/my-quotes" 
                className="text-primary-600 hover:text-primary-500"
              >
                My Quotes
              </Link>
              <Link 
                to="/app/analytics" 
                className="text-primary-600 hover:text-primary-500"
              >
                Analytics
              </Link>
            </div>
          </div>

          {/* Contact Support */}
          <div className="mt-8 pt-8 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              Still can't find what you're looking for?{' '}
              <a 
                href="mailto:support@quotemaster.pro" 
                className="text-primary-600 hover:text-primary-500"
              >
                Contact Support
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}