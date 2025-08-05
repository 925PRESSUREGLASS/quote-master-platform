import React, { useState } from 'react';
import { BarChart3, TrendingUp, Users, Quote, Mic, Calendar } from 'lucide-react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('7d');
  const [isLoading, setIsLoading] = useState(false);

  // Mock data - would be replaced with real API calls
  const stats = {
    totalQuotes: 142,
    totalVoiceRecordings: 38,
    totalViews: 2847,
    totalLikes: 524,
    avgQualityScore: 8.7,
    weeklyGrowth: 23.5,
  };

  const chartData = [
    { date: '2024-01-08', quotes: 12, voice: 3, views: 156 },
    { date: '2024-01-09', quotes: 15, voice: 5, views: 234 },
    { date: '2024-01-10', quotes: 8, voice: 2, views: 123 },
    { date: '2024-01-11', quotes: 20, voice: 7, views: 345 },
    { date: '2024-01-12', quotes: 18, voice: 4, views: 278 },
    { date: '2024-01-13', quotes: 25, voice: 8, views: 456 },
    { date: '2024-01-14', quotes: 22, voice: 6, views: 389 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">Track your quote generation and engagement metrics</p>
        </div>
        <div className="flex items-center space-x-3 mt-4 sm:mt-0">
          <select
            className="input"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <button className="btn btn-outline">
            <Calendar className="w-4 h-4 mr-2" />
            Custom Range
          </button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Quotes</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalQuotes}</p>
                <p className="text-sm text-green-600">+{stats.weeklyGrowth}% this week</p>
              </div>
              <div className="p-3 bg-primary-100 rounded-lg">
                <Quote className="w-6 h-6 text-primary-600" />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Voice Recordings</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalVoiceRecordings}</p>
                <p className="text-sm text-green-600">+12% this week</p>
              </div>
              <div className="p-3 bg-secondary-100 rounded-lg">
                <Mic className="w-6 h-6 text-secondary-600" />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Views</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalViews.toLocaleString()}</p>
                <p className="text-sm text-green-600">+8.3% this week</p>
              </div>
              <div className="p-3 bg-success-100 rounded-lg">
                <Users className="w-6 h-6 text-success-600" />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Likes</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalLikes}</p>
                <p className="text-sm text-green-600">+15.2% this week</p>
              </div>
              <div className="p-3 bg-warning-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-warning-600" />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Quality Score</p>
                <p className="text-2xl font-bold text-gray-900">{stats.avgQualityScore}/10</p>
                <p className="text-sm text-green-600">+0.3 this week</p>
              </div>
              <div className="p-3 bg-primary-100 rounded-lg">
                <BarChart3 className="w-6 h-6 text-primary-600" />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Growth Rate</p>
                <p className="text-2xl font-bold text-gray-900">+{stats.weeklyGrowth}%</p>
                <p className="text-sm text-green-600">vs last week</p>
              </div>
              <div className="p-3 bg-success-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-success-600" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold">Daily Activity</h3>
          </div>
          <div className="card-body">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="lg" />
              </div>
            ) : (
              <div className="space-y-4">
                {chartData.map((day, index) => (
                  <div key={day.date} className="flex items-center space-x-4">
                    <div className="text-sm text-gray-600 w-16">
                      {new Date(day.date).toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric' 
                      })}
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span>Quotes: {day.quotes}</span>
                        <span>Voice: {day.voice}</span>
                        <span>Views: {day.views}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full"
                          style={{ width: `${(day.quotes / 25) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Top Categories */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold">Top Categories</h3>
          </div>
          <div className="card-body">
            <div className="space-y-4">
              {[
                { name: 'Motivation', count: 45, percentage: 32 },
                { name: 'Life', count: 38, percentage: 27 },
                { name: 'Success', count: 29, percentage: 20 },
                { name: 'Wisdom', count: 18, percentage: 13 },
                { name: 'Happiness', count: 12, percentage: 8 },
              ].map((category) => (
                <div key={category.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-900">{category.name}</span>
                    <span className="text-xs text-gray-500">({category.count})</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-primary-600 h-2 rounded-full"
                        style={{ width: `${category.percentage}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 w-8">{category.percentage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Recent Activity</h3>
        </div>
        <div className="card-body">
          <div className="space-y-4">
            {[
              {
                type: 'quote',
                action: 'Generated quote',
                content: 'The only way to do great work is to love what you do.',
                time: '2 hours ago',
                engagement: { likes: 12, views: 45 },
              },
              {
                type: 'voice',
                action: 'Processed voice recording',
                content: 'morning-motivation.wav',
                time: '4 hours ago',
                engagement: { quotes: 3 },
              },
              {
                type: 'quote',
                action: 'Quote liked',
                content: 'Success is not final, failure is not fatal...',
                time: '6 hours ago',
                engagement: { likes: 8, views: 23 },
              },
            ].map((activity, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className={`p-2 rounded-lg ${
                  activity.type === 'quote' ? 'bg-primary-100' : 'bg-secondary-100'
                }`}>
                  {activity.type === 'quote' ? (
                    <Quote className={`w-4 h-4 ${
                      activity.type === 'quote' ? 'text-primary-600' : 'text-secondary-600'
                    }`} />
                  ) : (
                    <Mic className="w-4 h-4 text-secondary-600" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                  <p className="text-sm text-gray-600 truncate">{activity.content}</p>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-xs text-gray-500">{activity.time}</span>
                    {activity.engagement.likes && (
                      <span className="text-xs text-gray-500">
                        {activity.engagement.likes} likes
                      </span>
                    )}
                    {activity.engagement.views && (
                      <span className="text-xs text-gray-500">
                        {activity.engagement.views} views
                      </span>
                    )}
                    {activity.engagement.quotes && (
                      <span className="text-xs text-gray-500">
                        {activity.engagement.quotes} quotes generated
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}