import React, { useState } from 'react';
import { useTheme } from '@/store/ThemeContext';
import { useAnalytics } from '@/hooks/useAnalytics';
import { Moon, Sun, Monitor, Bell, Shield, Palette, Volume2 } from 'lucide-react';

export default function SettingsPage() {
  const { theme, updateTheme, toggleMode } = useTheme();
  const { isEnabled: analyticsEnabled, setEnabled: setAnalyticsEnabled } = useAnalytics();

  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: false,
      quote_generation: true,
      voice_processing: true,
      marketing: false,
    },
    privacy: {
      profile_public: false,
      quotes_public: true,
      analytics_tracking: analyticsEnabled,
    },
    preferences: {
      default_quote_style: 'inspirational',
      default_ai_model: 'gpt-4',
      auto_save: true,
      voice_auto_process: true,
    },
  });

  const updateSetting = (section: string, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section as keyof typeof prev],
        [key]: value,
      },
    }));
  };

  const handleAnalyticsToggle = (enabled: boolean) => {
    updateSetting('privacy', 'analytics_tracking', enabled);
    setAnalyticsEnabled(enabled);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Customize your Quote Master Pro experience</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Appearance */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Palette className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold">Appearance</h3>
            </div>
          </div>
          <div className="card-body space-y-4">
            {/* Theme Mode */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Theme Mode
              </label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => updateTheme({ mode: 'light' })}
                  className={`p-3 rounded-lg border-2 transition-colors ${
                    theme.mode === 'light'
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Sun className="w-5 h-5 mx-auto mb-1" />
                  <span className="text-sm">Light</span>
                </button>
                <button
                  onClick={() => updateTheme({ mode: 'dark' })}
                  className={`p-3 rounded-lg border-2 transition-colors ${
                    theme.mode === 'dark'
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Moon className="w-5 h-5 mx-auto mb-1" />
                  <span className="text-sm">Dark</span>
                </button>
                <button
                  onClick={() => updateTheme({ mode: 'system' })}
                  className={`p-3 rounded-lg border-2 transition-colors ${
                    theme.mode === 'system'
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Monitor className="w-5 h-5 mx-auto mb-1" />
                  <span className="text-sm">System</span>
                </button>
              </div>
            </div>

            {/* Font Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Font Size
              </label>
              <select
                className="input"
                value={theme.fontSize}
                onChange={(e) => updateTheme({ fontSize: e.target.value as any })}
              >
                <option value="sm">Small</option>
                <option value="md">Medium</option>
                <option value="lg">Large</option>
              </select>
            </div>

            {/* Animations */}
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Enable Animations
              </label>
              <input
                type="checkbox"
                checked={theme.animations}
                onChange={(e) => updateTheme({ animations: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Bell className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold">Notifications</h3>
            </div>
          </div>
          <div className="card-body space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Email Notifications
              </label>
              <input
                type="checkbox"
                checked={settings.notifications.email}
                onChange={(e) =>
                  updateSetting('notifications', 'email', e.target.checked)
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Push Notifications
              </label>
              <input
                type="checkbox"
                checked={settings.notifications.push}
                onChange={(e) =>
                  updateSetting('notifications', 'push', e.target.checked)
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Quote Generation Updates
              </label>
              <input
                type="checkbox"
                checked={settings.notifications.quote_generation}
                onChange={(e) =>
                  updateSetting('notifications', 'quote_generation', e.target.checked)
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Voice Processing Complete
              </label>
              <input
                type="checkbox"
                checked={settings.notifications.voice_processing}
                onChange={(e) =>
                  updateSetting('notifications', 'voice_processing', e.target.checked)
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Marketing Emails
              </label>
              <input
                type="checkbox"
                checked={settings.notifications.marketing}
                onChange={(e) =>
                  updateSetting('notifications', 'marketing', e.target.checked)
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>
          </div>
        </div>

        {/* Privacy */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold">Privacy</h3>
            </div>
          </div>
          <div className="card-body space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Public Profile
              </label>
              <input
                type="checkbox"
                checked={settings.privacy.profile_public}
                onChange={(e) =>
                  updateSetting('privacy', 'profile_public', e.target.checked)
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Public Quotes
              </label>
              <input
                type="checkbox"
                checked={settings.privacy.quotes_public}
                onChange={(e) =>
                  updateSetting('privacy', 'quotes_public', e.target.checked)
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Analytics Tracking
              </label>
              <input
                type="checkbox"
                checked={settings.privacy.analytics_tracking}
                onChange={(e) => handleAnalyticsToggle(e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Volume2 className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold">Preferences</h3>
            </div>
          </div>
          <div className="card-body space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Quote Style
              </label>
              <select
                className="input"
                value={settings.preferences.default_quote_style}
                onChange={(e) =>
                  updateSetting('preferences', 'default_quote_style', e.target.value)
                }
              >
                <option value="inspirational">Inspirational</option>
                <option value="motivational">Motivational</option>
                <option value="philosophical">Philosophical</option>
                <option value="humorous">Humorous</option>
                <option value="wisdom">Wisdom</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default AI Model
              </label>
              <select
                className="input"
                value={settings.preferences.default_ai_model}
                onChange={(e) =>
                  updateSetting('preferences', 'default_ai_model', e.target.value)
                }
              >
                <option value="gpt-4">GPT-4</option>
                <option value="claude-3">Claude 3</option>
                <option value="gemini">Gemini</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Auto-save Quotes
              </label>
              <input
                type="checkbox"
                checked={settings.preferences.auto_save}
                onChange={(e) =>
                  updateSetting('preferences', 'auto_save', e.target.checked)
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Auto-process Voice Recordings
              </label>
              <input
                type="checkbox"
                checked={settings.preferences.voice_auto_process}
                onChange={(e) =>
                  updateSetting('preferences', 'voice_auto_process', e.target.checked)
                }
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button className="btn btn-primary">
          Save All Settings
        </button>
      </div>
    </div>
  );
}