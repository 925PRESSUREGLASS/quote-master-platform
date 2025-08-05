import React, { useState, useRef } from 'react';
import { Mic, Square, Play, Pause, Upload, Trash2 } from 'lucide-react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function VoiceRecordingPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [transcription, setTranscription] = useState('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const chunks: BlobPart[] = [];
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        setAudioBlob(blob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      intervalRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  };

  const playRecording = () => {
    if (audioBlob && audioRef.current) {
      const audioUrl = URL.createObjectURL(audioBlob);
      audioRef.current.src = audioUrl;
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const pauseRecording = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const processRecording = async () => {
    if (!audioBlob) return;

    setIsProcessing(true);
    try {
      // Mock processing - would be real API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      setTranscription("This is where the transcribed text from your voice recording would appear. The AI would then process this text to generate meaningful quotes.");
    } catch (error) {
      console.error('Error processing recording:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const clearRecording = () => {
    setAudioBlob(null);
    setTranscription('');
    setRecordingTime(0);
    setIsPlaying(false);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Voice Recording</h1>
        <p className="text-gray-600">Record your voice to generate inspirational quotes</p>
      </div>

      {/* Recording Interface */}
      <div className="card">
        <div className="card-body text-center">
          {/* Recording Visualization */}
          <div className="mb-8">
            <div className="w-32 h-32 mx-auto bg-gradient-primary rounded-full flex items-center justify-center mb-4 relative">
              {isRecording && (
                <div className="absolute inset-0 rounded-full border-4 border-white animate-ping opacity-75" />
              )}
              <Mic className="w-16 h-16 text-white" />
            </div>
            
            {/* Voice Waves Animation */}
            {isRecording && (
              <div className="flex justify-center items-end space-x-1 h-12">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="voice-wave w-1"
                    style={{ height: '20px' }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Timer */}
          <div className="text-2xl font-mono text-gray-700 mb-6">
            {formatTime(recordingTime)}
          </div>

          {/* Controls */}
          <div className="flex justify-center space-x-4">
            {!isRecording ? (
              <button
                onClick={startRecording}
                className="btn btn-primary btn-lg"
                disabled={isProcessing}
              >
                <Mic className="w-6 h-6 mr-2" />
                Start Recording
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="btn btn-danger btn-lg"
              >
                <Square className="w-6 h-6 mr-2" />
                Stop Recording
              </button>
            )}

            {audioBlob && !isRecording && (
              <>
                {!isPlaying ? (
                  <button
                    onClick={playRecording}
                    className="btn btn-outline btn-lg"
                  >
                    <Play className="w-6 h-6 mr-2" />
                    Play
                  </button>
                ) : (
                  <button
                    onClick={pauseRecording}
                    className="btn btn-outline btn-lg"
                  >
                    <Pause className="w-6 h-6 mr-2" />
                    Pause
                  </button>
                )}

                <button
                  onClick={clearRecording}
                  className="btn btn-ghost btn-lg"
                >
                  <Trash2 className="w-6 h-6 mr-2" />
                  Clear
                </button>
              </>
            )}
          </div>

          {/* Process Button */}
          {audioBlob && !isRecording && (
            <div className="mt-6">
              <button
                onClick={processRecording}
                disabled={isProcessing}
                className="btn btn-secondary btn-lg"
              >
                {isProcessing ? (
                  <>
                    <LoadingSpinner size="sm" color="white" className="mr-2" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className="w-6 h-6 mr-2" />
                    Process Recording
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Transcription Results */}
      {transcription && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold">Transcription</h3>
          </div>
          <div className="card-body">
            <p className="text-gray-700 mb-4">{transcription}</p>
            <div className="flex space-x-3">
              <button className="btn btn-primary">
                Generate Quote from Text
              </button>
              <button className="btn btn-outline">
                Edit Transcription
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Tips for Better Results</h3>
        </div>
        <div className="card-body">
          <ul className="space-y-2 text-gray-600">
            <li>• Speak clearly and at a moderate pace</li>
            <li>• Record in a quiet environment</li>
            <li>• Share your thoughts, experiences, or wisdom</li>
            <li>• Aim for 30 seconds to 2 minutes of content</li>
            <li>• Express emotions and personal insights</li>
          </ul>
        </div>
      </div>

      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        onEnded={() => setIsPlaying(false)}
        style={{ display: 'none' }}
      />
    </div>
  );
}