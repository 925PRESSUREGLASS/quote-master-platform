import React from 'react';

function TestApp() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Quote Master Pro - Test Page
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          If you can see this, React is working!
        </p>
        <div className="space-y-4">
          <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
            Test Button
          </button>
          <div>
            <a
              href="/quotes"
              className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors inline-block"
            >
              Go to Quote Calculator
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TestApp;
