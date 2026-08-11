/**
 * Main Application Navbar with React Icons
 */

import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { 
  HiAcademicCap, 
  HiChartBar, 
  HiSparkles, 
  HiBookOpen, 
  HiLightningBolt, 
  HiLogout 
} from 'react-icons/hi'

export const Navbar = () => {
  const { user, logout } = useAuthStore()
  const location = useLocation()

  const navLinks = [
    { path: '/dashboard', label: 'Dashboard', icon: HiChartBar },
    { path: '/recommendations', label: 'AI Recommendations', icon: HiSparkles },
    { path: '/courses', label: 'Catalog', icon: HiBookOpen },
    { path: '/enrolled', label: 'My Courses', icon: HiAcademicCap },
    { path: '/activity', label: 'Activity Log', icon: HiLightningBolt },
  ]

  const isActive = (path: string) => {
    if (path === '/dashboard' && location.pathname === '/dashboard') return true
    if (path !== '/dashboard' && location.pathname.startsWith(path)) return true
    return false
  }

  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-gray-200/80 sticky top-0 z-50 shadow-xs transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 sm:h-20 gap-4">

          {/* Logo & Brand */}
          <div className="flex items-center gap-4 lg:gap-8 flex-shrink-0">
            <Link to="/dashboard" className="flex items-center gap-3 group flex-shrink-0">
              <div className="w-10 h-10 sm:w-11 sm:h-11 bg-gradient-to-tr from-primary-600 via-primary-700 to-indigo-800 rounded-2xl flex items-center justify-center text-white text-xl shadow-md group-hover:scale-105 group-hover:shadow-primary-500/25 transition-all duration-300">
                <HiAcademicCap className="w-6 h-6 text-white" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xl sm:text-2xl font-black tracking-tight text-gray-900 bg-gradient-to-r from-gray-900 via-gray-800 to-primary-900 bg-clip-text text-transparent">
                  SmartReco
                </span>
                <span className="hidden xl:inline-flex items-center gap-1 px-2.5 py-0.5 text-[11px] font-bold bg-primary-50 text-primary-700 rounded-full border border-primary-200/80 shadow-2xs">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-600 animate-pulse" />
                  AI Coach
                </span>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <nav className="hidden lg:flex items-center gap-1 xl:gap-2 flex-shrink-0">
              {navLinks.map((link) => {
                const Icon = link.icon
                const active = isActive(link.path)
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={`relative flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-semibold whitespace-nowrap transition-all duration-200 ${
                      active
                        ? 'bg-primary-50/90 text-primary-700 shadow-2xs border border-primary-100/90'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/70'
                    }`}
                  >
                    <Icon className={`w-4 h-4 flex-shrink-0 transition-colors ${active ? 'text-primary-600' : 'text-gray-400'}`} />
                    <span className="whitespace-nowrap">{link.label}</span>
                  </Link>
                )
              })}
            </nav>
          </div>

          {/* User profile & actions */}
          <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
            <div className="flex items-center gap-2 sm:gap-3 pl-2 sm:pl-4 border-l border-gray-200">
              <div 
                className="text-right hidden sm:block max-w-[120px] md:max-w-[160px] lg:max-w-[220px]" 
                title={user?.name || ''}
              >
                <div className="text-sm font-bold text-gray-900 leading-tight truncate whitespace-nowrap">
                  {user?.name}
                </div>
                <div className="text-[11px] text-gray-500 font-medium capitalize truncate whitespace-nowrap">
                  {user?.role || 'Learner'}
                </div>
              </div>

              <div className="relative flex-shrink-0">
                <div className="w-9 h-9 sm:w-10 sm:h-10 bg-gradient-to-tr from-primary-600 to-indigo-600 rounded-2xl flex items-center justify-center text-white font-extrabold text-sm shadow-sm ring-2 ring-primary-100">
                  {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white" />
              </div>

              <button
                onClick={() => logout()}
                className="p-2 text-gray-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all flex-shrink-0"
                title="Log out"
              >
                <HiLogout className="w-5 h-5" />
              </button>
            </div>
          </div>

        </div>

        {/* Mobile Navigation bar */}
        <div className="md:hidden flex items-center justify-between py-2 border-t border-gray-100 overflow-x-auto gap-2">
          {navLinks.map((link) => {
            const Icon = link.icon
            const active = isActive(link.path)
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  active ? 'bg-primary-50 text-primary-700 border border-primary-100 shadow-2xs' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${active ? 'text-primary-600' : 'text-gray-400'}`} />
                <span>{link.label}</span>
              </Link>
            )
          })}
        </div>

      </div>
    </header>
  )
}

export default Navbar
