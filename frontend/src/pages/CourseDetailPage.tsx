/**
 * Course Detail Page with Persistent DB Enrollment & React Icons
 */

import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import Navbar from '../components/layout/Navbar'
import { getProducts, Product } from '../api/products'
import { trackEvent, getMyEvents } from '../api/events'
import { useAuthStore } from '../store/authStore'
import { 
  HiCheckCircle, 
  HiClock, 
  HiDeviceMobile, 
  HiAcademicCap, 
  HiArrowLeft, 
  HiSparkles,
  HiBookmark,
  HiBadgeCheck
} from 'react-icons/hi'

export const CourseDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuthStore()

  const [course, setCourse] = useState<Product | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [enrolled, setEnrolled] = useState<boolean>(false)
  const [enrolling, setEnrolling] = useState<boolean>(false)

  useEffect(() => {
    const loadCourseAndEnrollment = async () => {
      setLoading(true)
      const [allProducts, myEvents] = await Promise.all([
        getProducts(),
        getMyEvents(100).catch(() => []),
      ])

      const found = allProducts.find((p) => p.id === id) || allProducts[0]
      setCourse(found)

      // Check if user has an 'enroll' event for this product in DB
      if (found && myEvents) {
        const hasEnrollEvent = myEvents.some(
          (evt) => (evt.event_type === 'enroll' || evt.event_type === 'enrollment') && evt.product_id === found.id
        )
        if (hasEnrollEvent) {
          setEnrolled(true)
        }
      }

      setLoading(false)

      // Track page view event in DB
      if (user && found) {
        trackEvent({
          user_id: user.id,
          session_id: 'session-' + Date.now(),
          event_type: 'view_product',
          product_id: found.id,
          event_metadata: { title: found.title, category: found.category }
        })
      }
    }
    loadCourseAndEnrollment()
  }, [id, user])

  const handleEnroll = async () => {
    if (!user || !course) return
    setEnrolling(true)

    // Store enrollment in PostgreSQL DB via event tracking
    await trackEvent({
      user_id: user.id,
      session_id: 'session-' + Date.now(),
      event_type: 'enroll',
      product_id: course.id,
      event_metadata: { 
        course_title: course.title, 
        price: course.price, 
        category: course.category,
        enrolled_at: new Date().toISOString() 
      }
    })

    setEnrolled(true)
    setEnrolling(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Navbar />
        <div className="flex-1 max-w-7xl mx-auto px-4 py-16 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Course Not Found</h2>
          <Link to="/courses" className="text-primary-600 font-semibold hover:underline flex items-center justify-center gap-1">
            <HiArrowLeft /> Back to Courses
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Back link */}
        <Link to="/courses" className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-primary-600 mb-6 transition-colors">
          <HiArrowLeft className="w-4 h-4" /> Back to Catalog
        </Link>

        {/* Course Header Banner */}
        <div className="bg-gradient-to-r from-gray-900 via-indigo-950 to-primary-950 rounded-3xl p-8 sm:p-12 text-white shadow-xl mb-8 relative overflow-hidden">
          <div className="max-w-3xl space-y-4">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-primary-600/80 text-white text-xs font-semibold rounded-full backdrop-blur-md">
                {course.category}
              </span>
              <span className="text-xs text-primary-200 capitalize font-medium">
                Level: {course.difficulty_level.toLowerCase()} • {course.duration_hours || 15} hours
              </span>
              {enrolled && (
                <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 text-xs font-semibold rounded-full border border-emerald-400/30 flex items-center gap-1">
                  <HiBadgeCheck className="w-4 h-4" /> Enrolled
                </span>
              )}
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
              {course.title}
            </h1>

            <p className="text-gray-300 text-base leading-relaxed">
              {course.description}
            </p>

            <div className="flex flex-wrap items-center gap-2 pt-2">
              {course.tags.map((tag) => (
                <span key={tag} className="text-xs bg-white/10 px-2.5 py-1 rounded-md text-primary-100 border border-white/10">
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Syllabus & Details */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Overview */}
            <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-100">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <HiSparkles className="w-5 h-5 text-primary-600" /> What You'll Learn
              </h2>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-gray-700">
                <li className="flex items-start gap-2">
                  <HiCheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /> Hands-on project-based curriculum
                </li>
                <li className="flex items-start gap-2">
                  <HiCheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /> Industry best practices & patterns
                </li>
                <li className="flex items-start gap-2">
                  <HiCheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /> Personalized AI learning feedback
                </li>
                <li className="flex items-start gap-2">
                  <HiCheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" /> Full access to source code
                </li>
              </ul>
            </div>

            {/* Curriculum Outline */}
            <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-100">
              <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <HiBookmark className="w-5 h-5 text-primary-600" /> Course Modules
              </h2>
              <div className="space-y-4">
                {[
                  { module: 'Module 1', title: 'Foundations & Architecture Setup', lessons: '4 lessons • 2h 30m' },
                  { module: 'Module 2', title: 'Core Skills & Hands-On Implementation', lessons: '8 lessons • 5h 15m' },
                  { module: 'Module 3', title: 'Advanced Patterns & Real-World Projects', lessons: '6 lessons • 4h 45m' },
                  { module: 'Module 4', title: 'Production Deployment & Evaluation', lessons: '5 lessons • 3h 10m' },
                ].map((m, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold text-primary-600 uppercase tracking-wider">{m.module}</span>
                      <h4 className="text-sm font-bold text-gray-900 mt-0.5">{m.title}</h4>
                    </div>
                    <span className="text-xs text-gray-500">{m.lessons}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Right Column: Enrollment Card */}
          <div>
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 sticky top-24 space-y-6">
              
              <div className="text-center pb-4 border-b border-gray-100">
                <div className="text-3xl font-extrabold text-gray-900">${course.price}</div>
                <div className="text-xs text-emerald-600 font-semibold mt-1">Full Lifetime Access</div>
              </div>

              {enrolled ? (
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center text-emerald-900 animate-fade-in space-y-1">
                  <HiBadgeCheck className="w-10 h-10 text-emerald-600 mx-auto" />
                  <div className="font-bold text-sm">Enrolled in Course</div>
                  <div className="text-xs text-emerald-700">You have full access to all course materials & lessons.</div>
                </div>
              ) : (
                <button
                  onClick={handleEnroll}
                  disabled={enrolling}
                  className="w-full py-3.5 bg-primary-600 hover:bg-primary-700 text-white font-bold text-sm rounded-xl shadow-md transition-all text-center flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {enrolling ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Enrolling…
                    </>
                  ) : (
                    'Enroll Now →'
                  )}
                </button>
              )}

              <div className="space-y-3 text-xs text-gray-600">
                <div className="flex items-center gap-2">
                  <HiClock className="w-4 h-4 text-gray-400" /> <strong>{course.duration_hours || 15} hours</strong> on-demand content
                </div>
                <div className="flex items-center gap-2">
                  <HiDeviceMobile className="w-4 h-4 text-gray-400" /> Access on mobile and desktop
                </div>
                <div className="flex items-center gap-2">
                  <HiAcademicCap className="w-4 h-4 text-gray-400" /> Certificate of completion
                </div>
              </div>

            </div>
          </div>

        </div>

      </main>
    </div>
  )
}

export default CourseDetailPage
