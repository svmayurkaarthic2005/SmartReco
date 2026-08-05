/**
 * Admin Layout
 * Dark sidebar with modern navigation
 */

import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Package, Users, Search, ArrowLeft, LogOut } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

const AdminLayout = () => {
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const navItems = [
    { path: '/admin', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/admin/products', label: 'Products', icon: Package },
    { path: '/admin/users', label: 'Users', icon: Users },
    { path: '/admin/traces', label: 'Traces', icon: Search },
  ]

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Dark Sidebar */}
      <aside className="w-64 bg-slate-900 text-white">
        <div className="p-6">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-lg">SR</span>
            </div>
            <div>
              <h1 className="text-lg font-bold">SmartReco</h1>
              <p className="text-xs text-gray-400">Admin Panel</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-primary-600 text-white font-semibold'
                      : 'text-gray-300 hover:bg-slate-800'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>

          {/* Back to App */}
          <div className="mt-8 pt-8 border-t border-slate-800">
            <Link
              to="/dashboard"
              className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back to App</span>
            </Link>
          </div>
        </div>

        {/* User section */}
        <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-slate-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-sm">
                {user?.name?.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">{user?.name}</p>
              <p className="text-xs text-gray-400 truncate">Administrator</p>
            </div>
          </div>
          
          <button
            onClick={() => logout()}
            className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {/* Top bar */}
        <div className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Admin Panel</h2>
              <p className="text-sm text-gray-600">Manage your SmartReco platform</p>
            </div>
            <div className="text-sm text-gray-600">
              Logged in as <strong>{user?.name}</strong>
            </div>
          </div>
        </div>

        {/* Page content */}
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default AdminLayout
