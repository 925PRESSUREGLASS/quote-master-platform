import React from 'react';
import { Link } from 'react-router-dom';
import { Quote, Mic, Brain, Sparkles } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="px-6 py-4">
        <div className="container flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gradient">Quote Master Pro</h1>
          <div className="flex items-center space-x-4">
            <Link to="/login" className="btn btn-ghost">
              Login
            </Link>
            <Link to="/register" className="btn btn-primary">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="section">
        <div className="container text-center">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-5xl font-bold text-gray-900 mb-6">
              AI-Powered Quote Generation with{' '}
              <span className="text-gradient">Psychology Integration</span>
            </h2>
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              Transform your thoughts into inspirational quotes using advanced AI,
              voice processing, and psychological insights. Create meaningful content
              that resonates with your audience.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register" className="btn btn-primary btn-lg">
                Start Creating Quotes
              </Link>
              <Link to="/app/quotes/generate" className="btn btn-outline btn-lg">
                Try Demo
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="section bg-white">
        <div className="container">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Powerful Features for Quote Creation
            </h3>
            <p className="text-lg text-gray-600">
              Everything you need to create, analyze, and share meaningful quotes
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Quote className="w-8 h-8 text-primary-600" />
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-2">
                AI Quote Generation
              </h4>
              <p className="text-gray-600">
                Generate unique, inspiring quotes using advanced AI models like GPT-4 and Claude
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-secondary-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Mic className="w-8 h-8 text-secondary-600" />
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-2">
                Voice Processing
              </h4>
              <p className="text-gray-600">
                Convert voice recordings to quotes with advanced speech recognition and analysis
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-success-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-success-600" />
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-2">
                Psychology Integration
              </h4>
              <p className="text-gray-600">
                Leverage psychological frameworks to create emotionally resonant content
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-warning-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-warning-600" />
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-2">
                Quality Analysis
              </h4>
              <p className="text-gray-600">
                Get detailed quality metrics and suggestions to improve your quotes
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="section bg-gradient-primary text-white">
        <div className="container text-center">
          <h3 className="text-3xl font-bold mb-4">
            Ready to Create Amazing Quotes?
          </h3>
          <p className="text-xl opacity-90 mb-8">
            Join thousands of creators who trust Quote Master Pro
          </p>
          <Link to="/register" className="btn bg-white text-primary-600 hover:bg-gray-100">
            Get Started for Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container text-center">
          <h4 className="text-xl font-bold mb-4">Quote Master Pro</h4>
          <p className="text-gray-400">
            AI-Powered Quote Generation Platform
          </p>
          <p className="text-gray-500 text-sm mt-4">
            © 2024 Quote Master Pro. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}