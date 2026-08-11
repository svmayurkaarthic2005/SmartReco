/**
 * Enrolled Courses Page
 * Displays active user enrollments and past unenrolled courses with Re-enroll / Unenroll capabilities
 */

import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Navbar } from '../components/layout/Navbar'
import { getMyEvents, trackEvent } from '../api/events'
import { getProducts, Product } from '../api/products'
import { refreshRecommendations } from '../api/recommendations'
import { useAuthStore } from '../store/authStore'
import { 
  HiAcademicCap, 
  HiBookOpen, 
  HiClock, 
  HiSparkles, 
  HiTrash, 
  HiCheckCircle,
  HiArrowRight,
  HiRefresh,
  HiPlusCircle
} from 'react-icons/hi'

export const EnrolledCoursesPage = () => {
  const user = useAuthStore((state) => state.user)
  const [activeCourses, setActiveCourses] = useState<Product[]>([])
  const [pastCourses, setPastCourses] = useState<Product[]>([])
  const [activeTab, setActiveTab] = useState<'active' | 'past'>('active')
  const [loading, setLoading] = useState(true)
  const [processingId, setProcessingId] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)

  const fetchEnrolledCourses = useCallback(async () => {
    setLoading(true)
    try {
      const [eventsData, productsData] = await Promise.all([
        getMyEvents(300),
        getProducts().catch(() => [])
      ])

      const productsMap = new Map((productsData || []).map(p => [p.id.toLowerCase(), p]))
      const productsByTitle = new Map((productsData || []).map(p => [p.title.toLowerCase(), p]))

      const activeSet = new Map<string, Product>()
      const pastSet = new Map<string, Product>()
      const processedProductIds = new Set<string>()

      if (eventsData) {
        for (const evt of eventsData) {
          const meta = (evt.metadata || (evt as any).event_metadata || {})
          const titleFromMeta = meta.course_title || meta.title
          const evtType = String(evt.event_type || '').toLowerCase()
          
          // Match product by ID or lowercased title
          let prod = evt.product_id ? productsMap.get(String(evt.product_id).toLowerCase()) : null
          if (!prod && titleFromMeta) {
            prod = productsByTitle.get(String(titleFromMeta).toLowerCase())
          }

          // Only set status and lock product when an ENROLL or UNENROLL event is found
          if (prod && !processedProductIds.has(prod.id)) {
            if (evtType === 'unenroll' || evtType === 'drop_course' || evtType.includes('unenroll')) {
              processedProductIds.add(prod.id)
              pastSet.set(prod.id, prod)
            } else if (evtType === 'enroll' || evtType === 'enrollment' || evtType.includes('enroll')) {
              processedProductIds.add(prod.id)
              activeSet.set(prod.id, prod)
            }
          }
        }
      }

      setActiveCourses(Array.from(activeSet.values()))
      setPastCourses(Array.from(pastSet.values()))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchEnrolledCourses()
  }, [fetchEnrolledCourses])

  const handleUnenroll = async (product: Product) => {
    setProcessingId(product.id)
    try {
      const meta = {
        course_title: product.title,
        category: product.category,
        action: 'unenroll',
        unenrolled_at: new Date().toISOString()
      }

      await trackEvent({
        user_id: user?.id,
        session_id: `sess-${Date.now()}`,
        event_type: 'unenroll',
        product_id: product.id,
        metadata: meta,
        event_metadata: meta
      })

      await refreshRecommendations().catch(() => {})

      setActiveCourses(prev => prev.filter(p => p.id !== product.id))
      setPastCourses(prev => [product, ...prev.filter(p => p.id !== product.id)])
      setNotification(`Unenrolled from "${product.title}". AI Recommendations have updated!`)
      
      setTimeout(() => setNotification(null), 5000)
    } catch (err) {
      console.error("Failed to unenroll:", err)
      alert("Failed to unenroll. Please try again.")
    } finally {
      setProcessingId(null)
    }
  }

  const handleReEnroll = async (product: Product) => {
    setProcessingId(product.id)
    try {
      const meta = {
        course_title: product.title,
        category: product.category,
        action: 're_enroll',
        re_enrolled_at: new Date().toISOString()
      }

      await trackEvent({
        user_id: user?.id,
        session_id: `sess-${Date.now()}`,
        event_type: 're_enroll',
        product_id: product.id,
        metadata: meta,
        event_metadata: meta
      })

      await refreshRecommendations().catch(() => {})

      setPastCourses(prev => prev.filter(p => p.id !== product.id))
      setActiveCourses(prev => [product, ...prev.filter(p => p.id !== product.id)])
      setNotification(`Re-enrolled in "${product.title}"! AI Recommendations updated.`)
      
      setTimeout(() => setNotification(null), 5000)
    } catch (err) {
      console.error("Failed to re-enroll:", err)
      alert("Failed to re-enroll. Please try again.")
    } finally {
      setProcessingId(null)
    }
  }

  const displayedCourses = activeTab === 'active' ? activeCourses : pastCourses

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
              <HiAcademicCap className="w-8 h-8 text-primary-600" />
              My Enrolled Courses
            </h1>
            <p className="text-gray-500 mt-1 text-sm">
              View active enrollments or previous courses. Unenrolling or re-enrolling automatically adjusts your AI recommendations.
            </p>
          </div>

          <Link
            to="/recommendations"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-primary-600 to-indigo-700 hover:from-primary-700 hover:to-indigo-800 text-white font-semibold text-sm rounded-xl shadow-sm transition-all"
          >
            <HiSparkles className="w-4 h-4 text-amber-300" /> View AI Recommendations
          </Link>
        </div>

        {/* Success Notification Banner */}
        {notification && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 px-5 py-3.5 rounded-2xl text-sm font-medium flex items-center gap-3 shadow-2xs">
            <HiCheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{notification}</span>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 border-b border-gray-200 pb-4">
          <button
            onClick={() => setActiveTab('active')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'active'
                ? 'bg-primary-600 text-white shadow-sm'
                : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            <HiCheckCircle className="w-4 h-4" />
            Active Enrollments ({activeCourses.length})
          </button>

          <button
            onClick={() => setActiveTab('past')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'past'
                ? 'bg-primary-600 text-white shadow-sm'
                : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            <HiRefresh className="w-4 h-4" />
            Previously Enrolled / Dropped ({pastCourses.length})
          </button>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="bg-white rounded-2xl p-12 text-center shadow-sm border border-gray-100">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Fetching your course history…</p>
          </div>
        ) : displayedCourses.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center shadow-sm border border-gray-100 max-w-2xl mx-auto space-y-4">
            <div className="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center mx-auto text-primary-600">
              <HiBookOpen className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-gray-900">
              {activeTab === 'active' ? 'No Active Enrollments' : 'No Previous Dropped Courses'}
            </h3>
            <p className="text-gray-500 text-sm leading-relaxed max-w-md mx-auto">
              Explore our catalog of 95+ courses across AI/ML, Web Dev, Cyber Security, and Cloud to start your learning path.
            </p>
            <Link
              to="/courses"
              className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-xl transition-all shadow-sm"
            >
              Browse Catalog <HiArrowRight className="w-4 h-4" />
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayedCourses.map((course) => (
              <div
                key={course.id}
                className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold px-3 py-1 bg-primary-50 text-primary-700 rounded-full border border-primary-100">
                      {course.category}
                    </span>
                    {activeTab === 'active' ? (
                      <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-md border border-emerald-100 flex items-center gap-1">
                        <HiCheckCircle className="w-3.5 h-3.5 text-emerald-600" /> Active Enrollment
                      </span>
                    ) : (
                      <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-md border border-amber-100 flex items-center gap-1">
                        <HiRefresh className="w-3.5 h-3.5 text-amber-600" /> Dropped / Past
                      </span>
                    )}
                  </div>

                  <h3 className="text-lg font-bold text-gray-900 leading-snug line-clamp-2">
                    <Link to={`/courses/${course.id}`} className="hover:text-primary-600 transition-colors">
                      {course.title}
                    </Link>
                  </h3>

                  <p className="text-gray-500 text-xs line-clamp-3 leading-relaxed">
                    {course.description}
                  </p>

                  <div className="flex items-center gap-4 text-xs text-gray-500 pt-2 border-t border-gray-100">
                    <span className="flex items-center gap-1">
                      <HiClock className="w-4 h-4 text-gray-400" /> {course.duration_hours || 20}h
                    </span>
                    <span className="font-semibold capitalize text-gray-700">
                      Level: {course.difficulty_level}
                    </span>
                  </div>
                </div>

                <div className="p-4 bg-gray-50/80 border-t border-gray-100 flex items-center justify-between gap-3">
                  <Link
                    to={`/courses/${course.id}`}
                    className="flex-1 text-center py-2 text-xs font-semibold text-gray-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors shadow-2xs"
                  >
                    View Details
                  </Link>

                  {activeTab === 'active' ? (
                    <button
                      onClick={() => handleUnenroll(course)}
                      disabled={processingId === course.id}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200/80 rounded-xl hover:bg-rose-100/80 transition-colors disabled:opacity-50"
                    >
                      <HiTrash className="w-3.5 h-3.5 text-rose-600" />
                      {processingId === course.id ? 'Processing…' : 'Unenroll'}
                    </button>
                  ) : (
                    <button
                      onClick={() => handleReEnroll(course)}
                      disabled={processingId === course.id}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 text-xs font-semibold text-primary-700 bg-primary-50 border border-primary-200/80 rounded-xl hover:bg-primary-100/80 transition-colors disabled:opacity-50"
                    >
                      <HiPlusCircle className="w-3.5 h-3.5 text-primary-600" />
                      {processingId === course.id ? 'Processing…' : 'Re-Enroll'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

      </main>
    </div>
  )
}
