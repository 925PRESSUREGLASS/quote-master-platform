import React, { useState } from 'react';
import { Search, Filter, Heart, Share2, BookmarkPlus, MoreHorizontal } from 'lucide-react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function MyQuotesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterBy, setFilterBy] = useState('all');
  const [isLoading, setIsLoading] = useState(false);

  // Mock data - would be replaced with real API calls
  const quotes = [
    {
      id: '1',
      text: 'The only way to do great work is to love what you do.',
      author: 'Steve Jobs',
      created_at: '2024-01-15T10:30:00Z',
      category: 'Motivation',
      likes: 42,
      shares: 12,
      isLiked: true,
      isFavorited: false,
    },
    {
      id: '2',
      text: 'Life is what happens to you while you\'re busy making other plans.',
      author: 'John Lennon',
      created_at: '2024-01-14T15:45:00Z',
      category: 'Life',
      likes: 38,
      shares: 8,
      isLiked: false,
      isFavorited: true,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Quotes</h1>
          <p className="text-gray-600">Manage and organize your generated quotes</p>
        </div>
        <button className="btn btn-primary mt-4 sm:mt-0">
          Generate New Quote
        </button>
      </div>

      {/* Search and Filters */}
      <div className="card">
        <div className="card-body">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search quotes..."
                className="input pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <select
                className="input"
                value={filterBy}
                onChange={(e) => setFilterBy(e.target.value)}
              >
                <option value="all">All Quotes</option>
                <option value="favorites">Favorites</option>
                <option value="popular">Most Popular</option>
                <option value="recent">Recently Created</option>
              </select>
              <button className="btn btn-outline">
                <Filter className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quotes Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="grid gap-6">
          {quotes.map((quote) => (
            <div key={quote.id} className="card hover:shadow-soft transition-shadow">
              <div className="card-body">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <blockquote className="text-lg text-gray-900 mb-2">
                      "{quote.text}"
                    </blockquote>
                    {quote.author && (
                      <cite className="text-sm text-gray-600">— {quote.author}</cite>
                    )}
                  </div>
                  <button className="btn btn-ghost btn-sm">
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <span className="badge badge-primary">{quote.category}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(quote.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      className={`btn btn-ghost btn-sm ${
                        quote.isLiked ? 'text-red-600' : 'text-gray-400'
                      }`}
                    >
                      <Heart className="w-4 h-4" />
                      <span className="ml-1">{quote.likes}</span>
                    </button>
                    <button className="btn btn-ghost btn-sm text-gray-400">
                      <Share2 className="w-4 h-4" />
                      <span className="ml-1">{quote.shares}</span>
                    </button>
                    <button
                      className={`btn btn-ghost btn-sm ${
                        quote.isFavorited ? 'text-yellow-600' : 'text-gray-400'
                      }`}
                    >
                      <BookmarkPlus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && quotes.length === 0 && (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <BookmarkPlus className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No quotes yet</h3>
          <p className="text-gray-600 mb-6">Start creating your first inspirational quote!</p>
          <button className="btn btn-primary">Generate Your First Quote</button>
        </div>
      )}
    </div>
  );
}