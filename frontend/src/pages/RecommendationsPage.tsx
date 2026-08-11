/**
 * AI Recommendations Page with React Icons
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/layout/Navbar'
import { getMyRecommendations, refreshRecommendations, getHistory } from '../api/recommendations'
import { RecommendationOutput, RecommendationHistoryItem } from '../types/recommendation'
import { 
  HiSparkles, 
  HiRefresh, 
  HiGlobe, 
  HiBadgeCheck, 
  HiPaperAirplane, 
  HiTrendingUp,
  HiMap,
  HiBookOpen,
  HiLightningBolt,
  HiArrowRight,
  HiLightBulb,
  HiTag
} from 'react-icons/hi'
import { FaYoutube } from 'react-icons/fa'

const getDirectVideoWatchUrl = (title: string) => {
  const t = (title || '').toLowerCase()
  if (t.includes('design system') || t.includes('figma') || t.includes('ui components') || t.includes('ui/ux')) {
    return 'https://www.youtube.com/watch?v=c9Wg6Cb_YlU' // freeCodeCamp (Build a Design System - Full Course)
  }
  if (t.includes('cyber') || t.includes('security') || t.includes('wireshark') || t.includes('hacking')) {
    return 'https://www.youtube.com/watch?v=3Kq1MIfTWCE' // NetworkChuck (Wireshark Packet Analysis)
  }
  if (t.includes('spark') || t.includes('data engineering') || t.includes('big data') || t.includes('kafka')) {
    return 'https://www.youtube.com/watch?v=qWru-b6m030' // freeCodeCamp (Data Engineering Pipeline Course)
  }
  if (t.includes('deep learning') || t.includes('neural') || t.includes('tensorflow') || t.includes('pytorch') || t.includes('ai')) {
    return 'https://www.youtube.com/watch?v=V_xro1bcAuA' // freeCodeCamp (PyTorch Deep Learning)
  }
  if (t.includes('android') || t.includes('kotlin') || t.includes('compose')) {
    return 'https://www.youtube.com/watch?v=F9UC9DY-vIU' // freeCodeCamp (Android Development with Kotlin)
  }
  if (t.includes('react') || t.includes('next.js') || t.includes('web') || t.includes('frontend')) {
    return 'https://www.youtube.com/watch?v=bMknfKXIFA8' // freeCodeCamp (React 18 Masterclass)
  }
  if (t.includes('sql') || t.includes('postgres') || t.includes('database')) {
    return 'https://www.youtube.com/watch?v=qw--VYLpxG4' // freeCodeCamp (SQL & PostgreSQL Tutorial)
  }
  if (t.includes('docker') || t.includes('kubernetes') || t.includes('aws') || t.includes('cloud')) {
    return 'https://www.youtube.com/watch?v=SOTamWNgDKc' // freeCodeCamp (AWS Solutions Architect)
  }
  if (t.includes('solidity') || t.includes('blockchain') || t.includes('web3')) {
    return 'https://www.youtube.com/watch?v=gyMwXuJrbVQ' // freeCodeCamp (Solidity 32-Hour Masterclass)
  }
  if (t.includes('unity') || t.includes('unreal') || t.includes('game')) {
    return 'https://www.youtube.com/watch?v=gB1F9G0JXOo' // freeCodeCamp (Unity C# Game Development)
  }

  // Fallback direct watch link
  return 'https://www.youtube.com/watch?v=c9Wg6Cb_YlU'
}

const getPersonaConfig = (personaStr: string) => {
  const normalized = (personaStr || '').toUpperCase().replace('-', '_')
  const labels: Record<string, string> = {
    EXPLORER: 'Curious Explorer',
    FOCUSED_BUILDER: 'Focused Skill Builder',
    CAREER_SWITCHER: 'Career Switcher',
    DEEP_DIVER: 'Deep Technical Diver',
    OVERWHELMED_LEARNER: 'Overwhelmed Learner',
    PRICE_SENSITIVE: 'Price Sensitive Learner',
    DROP_OFF_RISK: 'Re-engagement Priority',
  }
  const icons: Record<string, any> = {
    EXPLORER: HiGlobe,
    FOCUSED_BUILDER: HiBadgeCheck,
    CAREER_SWITCHER: HiPaperAirplane,
    DEEP_DIVER: HiTrendingUp,
    OVERWHELMED_LEARNER: HiLightBulb,
    PRICE_SENSITIVE: HiTag,
    DROP_OFF_RISK: HiLightningBolt,
  }
  const colors: Record<string, string> = {
    EXPLORER: 'bg-blue-50 text-blue-700 border-blue-200',
    FOCUSED_BUILDER: 'bg-purple-50 text-purple-700 border-purple-200',
    CAREER_SWITCHER: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    DEEP_DIVER: 'bg-amber-50 text-amber-700 border-amber-200',
    OVERWHELMED_LEARNER: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    PRICE_SENSITIVE: 'bg-orange-50 text-orange-700 border-orange-200',
    DROP_OFF_RISK: 'bg-rose-50 text-rose-700 border-rose-200',
  }

  const label = labels[normalized] || personaStr.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  const icon = icons[normalized] || HiBadgeCheck
  const color = colors[normalized] || 'bg-primary-50 text-primary-700 border-primary-200'

  return { label, icon, color }
}

export const RecommendationsPage = () => {
  const [recommendation, setRecommendation] = useState<RecommendationOutput | null>(null)
  const [history, setHistory] = useState<RecommendationHistoryItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [refreshing, setRefreshing] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const loadData = async (forceRefresh = false) => {
    setLoading(true)
    setError(null)
    try {
      let recoData: RecommendationOutput | null = null

      if (forceRefresh) {
        // Force-refresh path: always regenerate
        recoData = await refreshRecommendations().catch(() => null)
      } else {
        // Normal load: try to get existing/cached recommendation
        recoData = await getMyRecommendations().catch(() => null)

        // If nothing came back, auto-generate instead of showing an error
        if (!recoData) {
          recoData = await refreshRecommendations().catch(() => null)
        }
      }

      if (recoData) {
        setRecommendation(recoData)
        setError(null)
      } else {
        setError('Could not generate recommendations. Please ensure the backend is running and try again.')
      }

      const historyData = await getHistory(5).catch(() => [])
      setHistory(historyData || [])
    } catch (err: any) {
      setError('Failed to fetch recommendations. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    setError(null)
    try {
      console.log('[REFRESH] Calling POST /recommendations/refresh...')
      const freshData = await refreshRecommendations()
      console.log('[REFRESH] Got fresh data:', freshData?.ranked_products?.map((p: any) => p.title))
      setRecommendation(freshData)
      setError(null)
      const freshHistory = await getHistory(5).catch(() => [])
      setHistory(freshHistory)
    } catch (err: any) {
      console.error('[REFRESH] Error:', err?.response?.status, err?.response?.data || err?.message)
      if (!recommendation) {
        setError('Failed to refresh recommendations. Please try again.')
      }
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const currentPersona = getPersonaConfig(recommendation?.persona || 'FOCUSED_BUILDER')
  const PersonaIcon = currentPersona.icon

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
              <HiSparkles className="w-8 h-8 text-primary-600" /> AI Learning Recommendations
            </h1>
            <p className="text-gray-600 mt-1">
              Personalized recommendations powered by behavioral events and AI vector search.
            </p>
          </div>

          <button
            onClick={handleRefresh}
            disabled={refreshing || loading}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-semibold text-sm rounded-xl shadow-sm transition-all disabled:opacity-50"
          >
            {refreshing ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Re-analyzing Profile…
              </>
            ) : (
              <>
                <HiRefresh className="w-4 h-4" /> Refresh AI Analysis
              </>
            )}
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-2xl p-12 shadow-sm border border-gray-100 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-700 font-medium">Generating your AI recommendations...</p>
            <p className="text-gray-400 text-sm mt-1">Analyzing learning behavior, persona classification & course vector search — this takes a few seconds.</p>
          </div>
        )}

        {/* Error / Fallback State */}
        {!loading && error && !recommendation && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 mb-8 text-amber-900 flex items-start gap-4">
            <HiLightBulb className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-lg">Recommendations Notice</h3>
              <p className="text-sm text-amber-800 mt-1">{error}</p>
              <button
                onClick={handleRefresh}
                className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg text-sm font-semibold hover:bg-amber-700 transition-colors inline-flex items-center gap-2"
              >
                <HiRefresh className="w-4 h-4" /> Retry Now
              </button>
            </div>
          </div>
        )}

        {/* Main Recommendation Content */}
        {!loading && recommendation && (
          <div className="space-y-8">
            
            {/* Persona & Learning Goal Card */}
            <div className="bg-gradient-to-r from-primary-700 via-primary-800 to-indigo-900 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden">
              <div className="absolute top-0 right-0 transform translate-x-8 -translate-y-8 w-64 h-64 bg-white/10 rounded-full blur-2xl pointer-events-none" />
              
              <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
                <div className="lg:col-span-2 space-y-4">
                  <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/15 backdrop-blur-md border border-white/20 text-xs font-semibold text-primary-100">
                    <PersonaIcon className="w-4 h-4 text-primary-200" />
                    <span>Persona: {currentPersona.label}</span>
                  </div>

                  <h2 className="text-2xl sm:text-3xl font-bold tracking-tight leading-snug">
                    {recommendation.learning_goal || 'Master Key Industry Skills'}
                  </h2>

                  <p className="text-primary-100 text-sm leading-relaxed max-w-2xl">
                    {recommendation.personalized_story}
                  </p>

                  {recommendation.motivational_cta && (
                    <div className="pt-2 text-amber-300 font-semibold text-sm flex items-center gap-2">
                      <HiPaperAirplane className="w-4 h-4 text-amber-400" /> {recommendation.motivational_cta}
                    </div>
                  )}
                </div>

                {/* AI Confidence Meter */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 text-center">
                  <div className="text-xs text-primary-200 uppercase font-bold tracking-wider mb-2">AI Match Confidence</div>
                  <div className="text-4xl font-extrabold text-white mb-2">
                    {Math.round((recommendation.confidence || 0.85) * 100)}%
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-2 overflow-hidden mb-3">
                    <div
                      className="bg-emerald-400 h-full rounded-full transition-all duration-1000"
                      style={{ width: `${Math.round((recommendation.confidence || 0.85) * 100)}%` }}
                    />
                  </div>
                  <div className="text-xs text-primary-200">Based on recent activity & goals</div>
                </div>
              </div>
            </div>

            {/* Recovery Mode Alert (if present) */}
            {recommendation.is_recovery_mode && recommendation.recovery_result && (
              <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-rose-900 shadow-sm flex items-start gap-4">
                <HiLightningBolt className="w-6 h-6 text-rose-600 shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-bold text-base">Re-engagement AI Assist Active</h3>
                  <p className="text-sm text-rose-800 mt-1">{recommendation.recovery_result.recovery_narrative}</p>
                </div>
              </div>
            )}

            {/* AI Learning Roadmap */}
            {recommendation.roadmap && recommendation.roadmap.length > 0 && (
              <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-100">
                <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
                  <HiMap className="w-5 h-5 text-primary-600" /> Recommended Learning Path
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {recommendation.roadmap.map((step, idx) => {
                    const matchedProduct = (recommendation.ranked_products || []).find(p => 
                      p.title.toLowerCase().includes(step.toLowerCase()) || 
                      step.toLowerCase().includes(p.title.toLowerCase()) ||
                      (p.category && step.toLowerCase().includes(p.category.toLowerCase()))
                    )
                    const directVideoUrl = getDirectVideoWatchUrl(step)

                    return (
                      <div key={idx} className="bg-primary-50/50 border border-primary-100 rounded-xl p-4 relative flex flex-col justify-between hover:border-primary-300 transition-colors">
                        <div>
                          <div className="flex items-center justify-between mb-3">
                            <div className="w-7 h-7 bg-primary-600 text-white rounded-lg flex items-center justify-center font-bold text-xs shadow-sm">
                              {idx + 1}
                            </div>
                            {matchedProduct && (
                              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                                Course Available
                              </span>
                            )}
                          </div>
                          
                          {matchedProduct ? (
                            <Link to={`/courses/${matchedProduct.product_id}`} className="text-sm text-gray-900 font-bold hover:text-primary-600 leading-snug line-clamp-2 block transition-colors">
                              {step}
                            </Link>
                          ) : (
                            <p className="text-sm text-gray-900 font-bold leading-snug line-clamp-2">{step}</p>
                          )}
                        </div>
                        
                        <div className="mt-4 flex items-center gap-2 pt-2 border-t border-primary-100/60">
                          {matchedProduct && (
                            <Link
                              to={`/courses/${matchedProduct.product_id}`}
                              className="flex-1 inline-flex items-center justify-center gap-1 px-2.5 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs font-semibold rounded-lg transition-colors shadow-2xs"
                            >
                              Open Course <HiArrowRight className="w-3 h-3" />
                            </Link>
                          )}
                          <a
                            href={directVideoUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 inline-flex items-center justify-center gap-1 px-2.5 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-semibold rounded-lg border border-red-200/80 transition-colors shadow-2xs"
                          >
                            <FaYoutube className="w-3.5 h-3.5 text-red-600" /> Watch YT ↗
                          </a>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Ranked Recommended Courses */}
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <HiBookOpen className="w-6 h-6 text-primary-600" /> Recommended Courses ({recommendation.ranked_products?.length || 0})
                </h3>
                <Link to="/courses" className="text-sm font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-1">
                  View Full Catalog <HiArrowRight className="w-4 h-4" />
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {(recommendation.ranked_products || []).map((product, index) => (
                  <div
                    key={product.product_id || index}
                    className="bg-white rounded-2xl shadow-sm hover:shadow-lg transition-all border border-gray-100 p-6 flex flex-col justify-between group"
                  >
                    <div>
                      {/* Top tags */}
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <span className="px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-semibold rounded-md border border-primary-100">
                          {product.category || 'General'}
                        </span>
                        <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                          #{product.rank_position || index + 1} • {Math.round((product.final_score || 0.9) * 100)}% Match
                        </span>
                      </div>

                      <h4 className="text-base font-bold text-gray-900 group-hover:text-primary-600 transition-colors mb-2 line-clamp-2">
                        {product.title}
                      </h4>

                      <p className="text-gray-600 text-xs line-clamp-3 mb-4 leading-relaxed">
                        {product.description}
                      </p>

                      {/* AI explanation if available */}
                      {recommendation.product_explanations?.[product.product_id] && (
                        <div className="p-3 bg-gray-50 rounded-lg text-xs text-gray-600 border border-gray-100 mb-4">
                          <span className="font-semibold text-primary-700">Why recommended:</span>{' '}
                          {recommendation.product_explanations[product.product_id]}
                        </div>
                      )}
                    </div>

                    <div className="pt-4 border-t border-gray-100 flex items-center justify-between mt-2">
                      <div>
                        <div className="text-lg font-extrabold text-gray-900">${product.price || 49.99}</div>
                        <div className="text-xs text-gray-400 capitalize">{product.difficulty || 'Beginner'}</div>
                      </div>

                      <Link
                        to={`/courses/${product.product_id}`}
                        className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-semibold text-xs rounded-lg transition-colors shadow-sm flex items-center gap-1"
                      >
                        Explore Course <HiArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendation History */}
            {history.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-base font-bold text-gray-900 mb-4">Recommendation History</h3>
                <div className="divide-y divide-gray-100">
                  {history.map((item) => {
                    const pConfig = getPersonaConfig(item.persona)
                    const HistIcon = pConfig.icon
                    return (
                      <div key={item.id} className="py-3 flex items-center justify-between text-sm hover:bg-gray-50/50 px-2 rounded-xl transition-colors">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-xl border ${pConfig.color}`}>
                            <HistIcon className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="font-bold text-gray-900">
                              {pConfig.label}
                            </div>
                            <div className="text-xs text-gray-400 mt-0.5">
                              {new Date(item.generated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })} at {new Date(item.generated_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="font-extrabold text-primary-700">{Math.round(item.confidence * 100)}% Confidence</div>
                          <div className="text-xs text-gray-500 font-medium">{item.product_count} courses recommended</div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

          </div>
        )}

      </main>
    </div>
  )
}

export default RecommendationsPage
