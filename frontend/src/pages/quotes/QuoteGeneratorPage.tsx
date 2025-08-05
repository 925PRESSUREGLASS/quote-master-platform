import React, { useState } from 'react';
import { Sparkles, Settings, Download, Share } from 'lucide-react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function QuoteGeneratorPage() {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedQuote, setGeneratedQuote] = useState('');

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    
    setIsGenerating(true);
    
    // Simulate API call
    setTimeout(() => {
      setGeneratedQuote(`"${prompt}" - AI Generated Quote`);
      setIsGenerating(false);
    }, 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          AI Quote Generator
        </h1>
        <p className="text-gray-600">
          Transform your ideas into inspiring quotes with advanced AI
        </p>
      </div>

      {/* Generator Form */}
      <div className="card">
        <div className="card-body space-y-6">
          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
              What would you like your quote to be about?
            </label>
            <textarea
              id="prompt"
              rows={4}
              className="input"
              placeholder="Enter your topic, theme, or specific idea here..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={handleGenerate}
              disabled={!prompt.trim() || isGenerating}
              className="btn btn-primary flex items-center justify-center"
            >
              {isGenerating ? (
                <>
                  <LoadingSpinner size="sm" color="white" className="mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate Quote
                </>
              )}
            </button>
            
            <button className="btn btn-outline">
              <Settings className="w-4 h-4 mr-2" />
              Advanced Options
            </button>
          </div>
        </div>
      </div>

      {/* Generated Quote Display */}
      {generatedQuote && (
        <div className="card">
          <div className="card-body text-center">
            <blockquote className="text-2xl font-serif text-gray-800 italic mb-6">
              {generatedQuote}
            </blockquote>
            
            <div className="flex justify-center space-x-4">
              <button className="btn btn-outline">
                <Download className="w-4 h-4 mr-2" />
                Download
              </button>
              <button className="btn btn-outline">
                <Share className="w-4 h-4 mr-2" />
                Share
              </button>
              <button className="btn btn-primary">
                Save to Collection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}