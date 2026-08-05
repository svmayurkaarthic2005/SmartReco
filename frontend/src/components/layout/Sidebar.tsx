/**
 * Sidebar Navigation Component
 */

import { Link, useLocation } from 'react-router-dom'
import { Home, Search, Activity, Settings, LogOut } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

const Sidebar = () => {
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/courses', label: 'Browse', icon: Search },
    { path: '/activity', label: 'Activity', icon: Activity },
    { path: '/settings', label: 'Settings', icon: Settings },
  ]

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <Link to="/dashboard" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-purple-600 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-xl">SR</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">SmartReco</h1>
            <p className="text-xs text-gray-500">AI Learning Coach</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? 'bg-primary-50 text-primary-700 font-semibold'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-primary-600' : 'text-gray-500'}`} />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
            <span className="text-white font-semibold text-sm">
              {user?.name?.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-gray-900 truncate">{user?.name}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>
        
        <button
          onClick={() => logout()}
          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
