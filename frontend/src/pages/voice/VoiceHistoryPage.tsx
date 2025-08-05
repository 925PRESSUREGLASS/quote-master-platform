import React, { useState } from 'react';
import { Play, Download, Trash2, Clock, FileAudio, MessageSquare } from 'lucide-react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function VoiceHistoryPage() {
  const [isLoading, setIsLoading] = useState(false);

  // Mock data - would be replaced with real API calls
  const recordings = [
    {
      id: '1',
      filename: 'morning-thoughts.wav',
      duration: '2:34',
      created_at: '2024-01-15T08:30:00Z',
      file_size: '2.1 MB',
      status: 'processed',
      transcription: 'Success is not final, failure is not fatal: it is the courage to continue that counts.',
      quotes_generated: 3,
    },
    {
      id: '2',
      filename: 'life-wisdom.wav',
      duration: '1:47',
      created_at: '2024-01-14T19:15:00Z',
      file_size: '1.5 MB',
      status: 'processing',
      transcription: null,
      quotes_generated: 0,
    },
    {
      id: '3',
      filename: 'motivation-speech.wav',
      duration: '3:22',
      created_at: '2024-01-13T14:20:00Z',
      file_size: '2.8 MB',
      status: 'processed',
      transcription: 'The only impossible journey is the one you never begin.',
      quotes_generated: 5,
    },
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'processed':
        return <span className="badge badge-success">Processed</span>;
      case 'processing':
        return <span className="badge badge-warning">Processing</span>;
      case 'failed':
        return <span className="badge badge-error">Failed</span>;
      default:
        return <span className="badge badge-secondary">Unknown</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Voice History</h1>
          <p className="text-gray-600">Manage your voice recordings and generated quotes</p>
        </div>
        <button className="btn btn-primary mt-4 sm:mt-0">
          New Recording
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <div className="p-2 bg-primary-100 rounded-lg">
                <FileAudio className="w-6 h-6 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Recordings</p>
                <p className="text-2xl font-bold text-gray-900">{recordings.length}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <div className="p-2 bg-secondary-100 rounded-lg">
                <MessageSquare className="w-6 h-6 text-secondary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Quotes Generated</p>
                <p className="text-2xl font-bold text-gray-900">
                  {recordings.reduce((sum, r) => sum + r.quotes_generated, 0)}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="flex items-center">
              <div className="p-2 bg-success-100 rounded-lg">
                <Clock className="w-6 h-6 text-success-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Duration</p>
                <p className="text-2xl font-bold text-gray-900">8:43</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recordings List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="space-y-4">
          {recordings.map((recording) => (
            <div key={recording.id} className="card hover:shadow-soft transition-shadow">
              <div className="card-body">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 bg-gray-100 rounded-lg">
                      <FileAudio className="w-6 h-6 text-gray-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{recording.filename}</h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{recording.duration}</span>
                        <span>{recording.file_size}</span>
                        <span>{new Date(recording.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    {getStatusBadge(recording.status)}
                    
                    {recording.quotes_generated > 0 && (
                      <span className="text-sm text-gray-600">
                        {recording.quotes_generated} quotes
                      </span>
                    )}

                    <div className="flex space-x-2">
                      <button className="btn btn-ghost btn-sm">
                        <Play className="w-4 h-4" />
                      </button>
                      <button className="btn btn-ghost btn-sm">
                        <Download className="w-4 h-4" />
                      </button>
                      <button className="btn btn-ghost btn-sm text-red-600">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {recording.transcription && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Transcription:</h4>
                    <p className="text-gray-600">{recording.transcription}</p>
                    
                    {recording.quotes_generated > 0 && (
                      <div className="mt-3">
                        <button className="btn btn-primary btn-sm">
                          View Generated Quotes ({recording.quotes_generated})
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {recording.status === 'processing' && (
                  <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
                    <div className="flex items-center">
                      <LoadingSpinner size="sm" className="mr-2" />
                      <span className="text-sm text-yellow-800">
                        Processing recording... This may take a few minutes.
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && recordings.length === 0 && (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileAudio className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No recordings yet</h3>
          <p className="text-gray-600 mb-6">Start by recording your first voice message!</p>
          <button className="btn btn-primary">Record Voice Message</button>
        </div>
      )}
    </div>
  );
}