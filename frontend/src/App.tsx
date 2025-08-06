import { Routes, Route } from 'react-router-dom'
import { QuoteManagementPage } from '@/pages/quotes/QuoteManagementPage'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={
          <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                Quote Master Pro
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                AI-Powered Quote Generation Platform
              </p>
              <div className="space-y-4">
                <p className="text-gray-500">
                  🤖 AI Quote Generation with OpenAI & Claude
                </p>
                <p className="text-gray-500">
                  🎤 Voice Processing with Whisper AI
                </p>
                <p className="text-gray-500">
                  🧠 Psychology Integration & Emotional Analysis
                </p>
                <p className="text-gray-500">
                  📊 Real-time Analytics & Monitoring
                </p>
              </div>
              <div className="mt-8 space-x-4">
                <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
                  Get Started
                </button>
                <a 
                  href="/quotes"
                  className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors inline-block"
                >
                  Service Quotes
                </a>
              </div>
            </div>
          </div>
        } />
        <Route path="/quotes" element={<QuoteManagementPage />} />
      </Routes>
    </div>
  )
}

export default App