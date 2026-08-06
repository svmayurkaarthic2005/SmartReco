/**
 * Main App Component
 * Configures routing and protected routes
 */

import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import { useEffect, useRef } from 'react'
import { trackEvent } from './api/events'

// Pages
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import CoursesPage from './pages/CoursesPage'
import CourseDetailPage from './pages/CourseDetailPage'
import ActivityPage from './pages/ActivityPage'
import RecommendationsPage from './pages/RecommendationsPage'
import { EnrolledCoursesPage } from './pages/EnrolledCoursesPage'

// Components
import { ProtectedRoute } from './components/layout/ProtectedRoute'

/**
 * Global Page Navigation Tracker
 * Detects page shifts across routes and logs exact dynamic dwell time
 */
const RouteTracker = () => {
  const location = useLocation()
  const user = useAuthStore((state) => state.user)
  const prevPageRef = useRef<{ path: string; label: string; startTime: number } | null>(null)

  useEffect(() => {
    if (!user) return

    const pagePath = location.pathname
    let pageLabel = 'Dashboard Page'

    if (pagePath === '/dashboard') pageLabel = 'Dashboard Page'
    else if (pagePath === '/recommendations') pageLabel = 'AI Recommendations Page'
    else if (pagePath === '/courses') pageLabel = 'Course Catalog Page'
    else if (pagePath === '/enrolled') pageLabel = 'My Courses & Enrollments Page'
    else if (pagePath === '/activity') pageLabel = 'Activity & Telemetry Log Page'
    else if (pagePath.startsWith('/courses/')) pageLabel = 'Course Details View'

    const now = Date.now()

    // 1. If we were on a previous page, log the exact dwell time spent on that previous page
    if (prevPageRef.current && prevPageRef.current.path !== pagePath) {
      const actualDwell = Math.max(1, Math.round((now - prevPageRef.current.startTime) / 1000))
      trackEvent({
        user_id: user.id,
        session_id: 'session-' + now,
        event_type: 'time_on_page',
        dwell_time: actualDwell,
        metadata: {
          page_url: prevPageRef.current.path,
          page_name: prevPageRef.current.label,
          dwell_time: actualDwell,
          action: 'page_exit'
        },
        event_metadata: {
          page_url: prevPageRef.current.path,
          page_name: prevPageRef.current.label,
          dwell_time: actualDwell,
          action: 'page_exit'
        }
      }).catch(() => {})
    }

    // 2. Track initial view event for newly entered page
    trackEvent({
      user_id: user.id,
      session_id: 'session-' + now,
      event_type: 'view_category',
      metadata: {
        page_url: pagePath,
        page_name: pageLabel,
        action: 'page_navigation'
      },
      event_metadata: {
        page_url: pagePath,
        page_name: pageLabel,
        action: 'page_navigation'
      }
    }).catch(() => {})

    // Update reference for current active page
    prevPageRef.current = {
      path: pagePath,
      label: pageLabel,
      startTime: now
    }
  }, [location.pathname, user?.id])

  return null
}

function App() {
  const { isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading SmartReco...</p>
        </div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <RouteTracker />
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/courses" element={<CoursesPage />} />
          <Route path="/courses/:id" element={<CourseDetailPage />} />
          <Route path="/enrolled" element={<EnrolledCoursesPage />} />
          <Route path="/activity" element={<ActivityPage />} />
        </Route>

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}

// Simple 404 page
const NotFoundPage = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
      <p className="text-xl text-gray-600 mb-8">Page not found</p>
      <a href="/dashboard" className="btn-primary">
        Go to Dashboard
      </a>
    </div>
  </div>
)

export default App
