import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Quote,
  Mic,
  BarChart3,
  User,
  Settings,
  Shield,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { UserRole } from '@/types';

const navigation = [
  {
    name: 'Dashboard',
    href: '/app',
    icon: LayoutDashboard,
  },
  {
    name: 'Generate Quote',
    href: '/app/quotes/generate',
    icon: Quote,
  },
  {
    name: 'My Quotes',
    href: '/app/quotes/my-quotes',
    icon: Quote,
  },
  {
    name: 'Voice Recording',
    href: '/app/voice/record',
    icon: Mic,
  },
  {
    name: 'Voice History',
    href: '/app/voice/history',
    icon: Mic,
  },
  {
    name: 'Analytics',
    href: '/app/analytics',
    icon: BarChart3,
  },
  {
    name: 'Profile',
    href: '/app/profile',
    icon: User,
  },
  {
    name: 'Settings',
    href: '/app/settings',
    icon: Settings,
  },
];

const adminNavigation = [
  {
    name: 'Admin Panel',
    href: '/app/admin',
    icon: Shield,
  },
];

export default function Sidebar() {
  const { user } = useAuth();
  const isAdmin = user?.role === UserRole.ADMIN || user?.role === UserRole.MODERATOR;

  return (
    <aside className="fixed top-16 left-0 h-[calc(100vh-4rem)] w-64 bg-white border-r border-gray-200 z-40">
      <nav className="h-full overflow-y-auto px-3 py-6">
        <ul className="space-y-2">
          {navigation.map((item) => (
            <li key={item.name}>
              <NavLink
                to={item.href}
                end={item.href === '/app'}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'nav-link-active' : 'nav-link-inactive'}`
                }
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </NavLink>
            </li>
          ))}

          {/* Admin Navigation */}
          {isAdmin && (
            <>
              <li className="pt-4">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide px-3 py-2">
                  Administration
                </div>
              </li>
              {adminNavigation.map((item) => (
                <li key={item.name}>
                  <NavLink
                    to={item.href}
                    className={({ isActive }) =>
                      `nav-link ${isActive ? 'nav-link-active' : 'nav-link-inactive'}`
                    }
                  >
                    <item.icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </NavLink>
                </li>
              ))}
            </>
          )}
        </ul>
      </nav>
    </aside>
  );
}