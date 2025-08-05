import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Users, FileText, BarChart3, Settings, Shield } from 'lucide-react';

// Placeholder admin components
const AdminDashboard = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">Admin Dashboard</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div className="card">
        <div className="card-body">
          <div className="flex items-center">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Users className="w-6 h-6 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Users</p>
              <p className="text-2xl font-bold text-gray-900">1,247</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="card">
        <div className="card-body">
          <div className="flex items-center">
            <div className="p-2 bg-secondary-100 rounded-lg">
              <FileText className="w-6 h-6 text-secondary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Quotes</p>
              <p className="text-2xl font-bold text-gray-900">15,892</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="flex items-center">
            <div className="p-2 bg-success-100 rounded-lg">
              <BarChart3 className="w-6 h-6 text-success-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Sessions</p>
              <p className="text-2xl font-bold text-gray-900">342</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="flex items-center">
            <div className="p-2 bg-warning-100 rounded-lg">
              <Shield className="w-6 h-6 text-warning-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending Reviews</p>
              <p className="text-2xl font-bold text-gray-900">23</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Recent Users</h3>
        </div>
        <div className="card-body">
          <p className="text-gray-500">User management interface would go here.</p>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">System Health</h3>
        </div>
        <div className="card-body">
          <p className="text-gray-500">System monitoring dashboard would go here.</p>
        </div>
      </div>
    </div>
  </div>
);

const UserManagement = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
    <div className="card">
      <div className="card-body">
        <p className="text-gray-500">User management interface would be implemented here.</p>
      </div>
    </div>
  </div>
);

const QuoteModeration = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">Quote Moderation</h2>
    <div className="card">
      <div className="card-body">
        <p className="text-gray-500">Quote moderation interface would be implemented here.</p>
      </div>
    </div>
  </div>
);

const SystemSettings = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">System Settings</h2>
    <div className="card">
      <div className="card-body">
        <p className="text-gray-500">System configuration interface would be implemented here.</p>
      </div>
    </div>
  </div>
);

export default function AdminPage() {
  return (
    <div className="space-y-6">
      {/* Admin Header */}
      <div className="bg-gradient-to-r from-red-500 to-red-700 text-white rounded-xl p-6">
        <h1 className="text-2xl font-bold mb-2">Administration Panel</h1>
        <p className="opacity-90">Manage users, content, and system settings</p>
      </div>

      {/* Admin Navigation */}
      <div className="card">
        <div className="card-body">
          <nav className="flex space-x-6">
            <a href="/app/admin" className="nav-link nav-link-active">
              Dashboard
            </a>
            <a href="/app/admin/users" className="nav-link nav-link-inactive">
              Users
            </a>
            <a href="/app/admin/quotes" className="nav-link nav-link-inactive">
              Quotes
            </a>
            <a href="/app/admin/settings" className="nav-link nav-link-inactive">
              Settings
            </a>
          </nav>
        </div>
      </div>

      {/* Admin Routes */}
      <Routes>
        <Route index element={<AdminDashboard />} />
        <Route path="users" element={<UserManagement />} />
        <Route path="quotes" element={<QuoteModeration />} />
        <Route path="settings" element={<SystemSettings />} />
      </Routes>
    </div>
  );
}