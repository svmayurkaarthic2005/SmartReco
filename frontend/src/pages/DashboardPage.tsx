/**
 * Main Learner Dashboard Page with React Icons
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/layout/Navbar'
import { useAuthStore } from '../store/authStore'
import { getMyRecommendations } from '../api/recommendations'
import { getProducts, Product } from '../api/products'
import { RecommendationOutput } from '../types/recommendation'
import { 
  HiSparkles, 
  HiBookOpen, 
  HiLightningBolt, 
  HiGlobe, 
  HiBadgeCheck, 
  HiPaperAirplane, 
  HiTrendingUp,
  HiFire,
  HiArrowRight,
  HiChartBar
} from 'react-icons/hi'

const personaBadges: Record<string, { label: string; icon: any; bg: string }> = {
  EXPLORER: { label: 'Curious Explorer', icon: HiGlobe, bg: 'from-blue-500 to-indigo-600' },
  FOCUSED_BUILDER: { label: 'Focused Builder', icon: HiBadgeCheck, bg: 'from-purple-500 to-indigo-600' },
  CAREER_SWITCHER: { label: 'Career Switcher', icon: HiPaperAirplane, bg: 'from-emerald-500 to-teal-600' },
  DEEP_DIVER: { label: 'Deep Technical Diver', icon: HiTrendingUp, bg: 'from-amber-500 to-orange-600' },
}

export const DashboardPage = () => {
  const { user } = useAuthStore()
  const [recommendation, setRecommendation] = useState<RecommendationOutput | null>(null)
  const [featuredCourses, setFeaturedCourses] = useState<Product[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true)
      const [reco, courses] = await Promise.all([
        getMyRecommendations().catch(() => null),
        getProducts().catch(() => []),
      ])

      setRecommendation(reco)
      if (reco && reco.ranked_products && reco.ranked_products.length > 0) {
        const recoIds = reco.ranked_products.map(r => r.product_id)
        const recoFeatured = courses.filter(c => recoIds.includes(c.id)).slice(0, 3)
        setFeaturedCourses(recoFeatured.length > 0 ? recoFeatured : courses.slice(0, 3))
      } else {
        setFeaturedCourses(courses.slice(0, 3))
      }
      setLoading(false)
    }
    fetchDashboardData()
  }, [])

  const userPersonaKey = recommendation?.persona?.toUpperCase() || 'FOCUSED_BUILDER'
  const activePersona = personaBadges[userPersonaKey] || personaBadges.FOCUSED_BUILDER
  const PersonaIcon = activePersona.icon

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

        {/* Welcome Hero Banner */}
        <div className="bg-gradient-to-r from-primary-700 via-primary-800 to-indigo-900 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 transform translate-x-12 -translate-y-12 w-80 h-80 bg-white/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/15 backdrop-blur-md rounded-full text-xs font-semibold text-primary-100 border border-white/20">
                <PersonaIcon className="w-4 h-4 text-primary-200" />
                <span>Persona: {activePersona.label}</span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
                Welcome back, {user?.name || 'Learner'}! 👋
              </h1>

              <p className="text-primary-100 text-sm max-w-xl leading-relaxed">
                SmartReco has analyzed your learning behavior to curate personalized AI recommendations and tailored course roadmaps for you.
              </p>
            </div>

            <Link
              to="/recommendations"
              className="inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-white text-primary-700 hover:bg-primary-50 font-bold text-sm rounded-2xl shadow-lg transition-all shrink-0 hover:scale-105"
            >
              <HiSparkles className="w-4 h-4 text-primary-600" /> View AI Recommendations
            </Link>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Card 1: Recommendations */}
          <div className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-all border border-gray-100 flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 bg-primary-50 text-primary-600 rounded-xl flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform">
                <HiSparkles className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">AI Recommendations</h3>
              <p className="text-gray-600 text-xs leading-relaxed mb-4">
                View your AI-generated learning goal, persona breakdown, and ranked course matching scores.
              </p>
            </div>
            <Link to="/recommendations" className="text-xs font-bold text-primary-600 hover:text-primary-700 flex items-center gap-1">
              View recommendations <HiArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Card 2: Browse Courses */}
          <div className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-all border border-gray-100 flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform">
                <HiBookOpen className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">Browse Catalog</h3>
              <p className="text-gray-600 text-xs leading-relaxed mb-4">
                Search through our catalog of tech courses across Web Dev, AI/ML, Cloud, and Data Science.
              </p>
            </div>
            <Link to="/courses" className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
              Explore catalog <HiArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Card 3: Behavioral Activity */}
          <div className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-all border border-gray-100 flex flex-col justify-between group">
            <div>
              <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform">
                <HiLightningBolt className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">Your Activity Log</h3>
              <p className="text-gray-600 text-xs leading-relaxed mb-4">
                Track real-time event logs, search queries, page views, and your behavioral MD5 hash signature.
              </p>
            </div>
            <Link to="/activity" className="text-xs font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1">
              View activity stream <HiArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

        </div>

        {/* Featured Courses Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <HiFire className="w-5 h-5 text-amber-500" /> Featured Courses
            </h2>
            <Link to="/courses" className="text-sm font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1">
              Browse All Courses <HiArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {loading ? (
            <div className="text-center py-12 bg-white rounded-2xl border border-gray-100">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
              <p className="text-xs text-gray-400">Loading courses...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {featuredCourses.map((course) => (
                <div key={course.id} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between group">
                  <div>
                    <span className="px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-semibold rounded-md border border-primary-100">
                      {course.category}
                    </span>
                    <h3 className="text-base font-bold text-gray-900 group-hover:text-primary-600 transition-colors mt-3 mb-2 line-clamp-1">
                      {course.title}
                    </h3>
                    <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed mb-4">
                      {course.description}
                    </p>
                  </div>
                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <span className="font-extrabold text-gray-900 text-base">${course.price}</span>
                    <Link to={`/courses/${course.id}`} className="text-xs font-bold text-primary-600 hover:text-primary-700 flex items-center gap-1">
                      Details <HiArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AI Learning Personas Info Card */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-100">
          <h2 className="text-lg font-bold text-gray-900 mb-2 flex items-center gap-2">
            <HiChartBar className="w-5 h-5 text-primary-600" /> How SmartReco AI Adapts to You
          </h2>
          <p className="text-xs text-gray-500 mb-6">Our LangGraph AI agent automatically classifies your learning persona based on event data:</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { title: 'Curious Explorer', icon: HiGlobe, desc: 'Browses diverse topics, seeks broad introductory knowledge.' },
              { title: 'Focused Builder', icon: HiBadgeCheck, desc: 'Consistently focuses on a single tech stack to complete projects.' },
              { title: 'Career Switcher', icon: HiPaperAirplane, desc: 'Fast-tracks core skills needed to transition into tech roles.' },
              { title: 'Deep Diver', icon: HiTrendingUp, desc: 'Engages with advanced, specialized technical concepts.' },
            ].map((p) => {
              const Icon = p.icon
              return (
                <div key={p.title} className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                  <Icon className="w-6 h-6 text-primary-600 mb-2" />
                  <div className="font-bold text-sm text-gray-900">{p.title}</div>
                  <div className="text-xs text-gray-500 mt-1 leading-relaxed">{p.desc}</div>
                </div>
              )
            })}
          </div>
        </div>

      </main>
    </div>
  )
}

export default DashboardPage
