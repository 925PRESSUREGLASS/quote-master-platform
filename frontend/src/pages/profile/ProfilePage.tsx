import React, { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Camera, Mail, User, Calendar, Award } from 'lucide-react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function ProfilePage() {
  const { user, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    username: user?.username || '',
    bio: user?.bio || '',
    avatar_url: user?.avatar_url || '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await updateProfile(formData);
      setIsEditing(false);
    } catch (error) {
      // Error handling is done in the AuthContext
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      full_name: user?.full_name || '',
      username: user?.username || '',
      bio: user?.bio || '',
      avatar_url: user?.avatar_url || '',
    });
    setIsEditing(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
        <p className="text-gray-600">Manage your account information and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="card-header">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Personal Information</h3>
                {!isEditing ? (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="btn btn-outline btn-sm"
                  >
                    Edit Profile
                  </button>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleCancel}
                      className="btn btn-ghost btn-sm"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={isLoading}
                      className="btn btn-primary btn-sm"
                    >
                      {isLoading ? (
                        <LoadingSpinner size="sm" color="white" className="mr-2" />
                      ) : null}
                      Save Changes
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="card-body">
              {/* Avatar */}
              <div className="flex items-center space-x-6 mb-6">
                <div className="relative">
                  {user?.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt={user.display_name}
                      className="w-20 h-20 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center">
                      <User className="w-10 h-10 text-gray-400" />
                    </div>
                  )}
                  {isEditing && (
                    <button className="absolute bottom-0 right-0 p-1 bg-primary-600 text-white rounded-full hover:bg-primary-700">
                      <Camera className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">
                    {user?.display_name}
                  </h3>
                  <p className="text-gray-600">{user?.email}</p>
                  <span className="badge badge-primary mt-2">{user?.role}</span>
                </div>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        className="input"
                        value={formData.full_name}
                        onChange={(e) =>
                          setFormData({ ...formData, full_name: e.target.value })
                        }
                      />
                    ) : (
                      <p className="text-gray-900">{user?.full_name || 'Not provided'}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Username
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        className="input"
                        value={formData.username}
                        onChange={(e) =>
                          setFormData({ ...formData, username: e.target.value })
                        }
                      />
                    ) : (
                      <p className="text-gray-900">{user?.username || 'Not provided'}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bio
                  </label>
                  {isEditing ? (
                    <textarea
                      className="input"
                      rows={3}
                      placeholder="Tell us about yourself..."
                      value={formData.bio}
                      onChange={(e) =>
                        setFormData({ ...formData, bio: e.target.value })
                      }
                    />
                  ) : (
                    <p className="text-gray-900">{user?.bio || 'No bio provided'}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <div className="flex items-center space-x-2">
                    <Mail className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-900">{user?.email}</span>
                    {user?.is_verified && (
                      <span className="badge badge-success">Verified</span>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Member Since
                  </label>
                  <div className="flex items-center space-x-2">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-900">
                      {user?.created_at
                        ? new Date(user.created_at).toLocaleDateString()
                        : 'Unknown'}
                    </span>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Stats Sidebar */}
        <div className="space-y-6">
          {/* Activity Stats */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold">Activity</h3>
            </div>
            <div className="card-body space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Quotes Generated</span>
                <span className="font-semibold">{user?.total_quotes_generated || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Voice Recordings</span>
                <span className="font-semibold">{user?.total_voice_requests || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Last Login</span>
                <span className="font-semibold">
                  {user?.last_login_at
                    ? new Date(user.last_login_at).toLocaleDateString()
                    : 'Never'}
                </span>
              </div>
            </div>
          </div>

          {/* Subscription */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold">Subscription</h3>
            </div>
            <div className="card-body">
              <div className="flex items-center space-x-2 mb-3">
                <Award className="w-5 h-5 text-primary-600" />
                <span className="font-semibold text-primary-600">
                  {user?.subscription_tier || 'Free'}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Enjoy all the features of your current plan.
              </p>
              <button className="btn btn-primary w-full">
                Upgrade Plan
              </button>
            </div>
          </div>

          {/* Account Status */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold">Account Status</h3>
            </div>
            <div className="card-body space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Email Verified</span>
                {user?.is_verified ? (
                  <span className="badge badge-success">Yes</span>
                ) : (
                  <span className="badge badge-warning">No</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Account Active</span>
                {user?.is_active ? (
                  <span className="badge badge-success">Yes</span>
                ) : (
                  <span className="badge badge-error">No</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}