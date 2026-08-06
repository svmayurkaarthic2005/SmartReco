/**
 * User Activity & Behavioral Log — fully featured
 */

import { useState, useEffect, useCallback } from 'react'
import Navbar from '../components/layout/Navbar'
import { getMyEvents, getMyEventHash, UserEvent, EventHashResponse } from '../api/events'
import { getProducts, Product } from '../api/products'
import {
  HiLightningBolt,
  HiEye,
  HiCursorClick,
  HiSearch,
  HiClock,
  HiTag,
  HiRefresh,
  HiFilter,
  HiTrendingUp,
  HiAcademicCap,
  HiCheckCircle,
  HiChevronDown,
  HiX,
} from 'react-icons/hi'

const EVENT_CONFIG: Record<string, { label: string; color: string; dot: string; icon: any }> = {
  view_product:    { label: 'View Product',   color: 'bg-blue-50 text-blue-700 border-blue-200',     dot: 'bg-blue-500',    icon: HiEye },
  view_category:  { label: 'Browse Category', color: 'bg-indigo-50 text-indigo-700 border-indigo-200', dot: 'bg-indigo-400', icon: HiEye },
  click:          { label: 'Click',           color: 'bg-purple-50 text-purple-700 border-purple-200', dot: 'bg-purple-500', icon: HiCursorClick },
  search:         { label: 'Search',          color: 'bg-amber-50 text-amber-700 border-amber-200',   dot: 'bg-amber-500',   icon: HiSearch },
  enroll:         { label: 'Enrollment',      color: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500', icon: HiAcademicCap },
  enrollment:     { label: 'Enrollment',      color: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500', icon: HiAcademicCap },
  re_enroll:      { label: 'Re-Enrollment 🔄',color: 'bg-emerald-100 text-emerald-900 border-emerald-300 font-bold', dot: 'bg-emerald-600', icon: HiRefresh },
  lesson_complete:{ label: 'Lesson Completed',color: 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold', dot: 'bg-emerald-600', icon: HiCheckCircle },
  module_complete:{ label: 'Module Completed',color: 'bg-emerald-100 text-emerald-900 border-emerald-400 font-extrabold', dot: 'bg-emerald-700', icon: HiCheckCircle },
  unenroll:       { label: 'Unenrolled',      color: 'bg-rose-50 text-rose-700 border-rose-200',     dot: 'bg-rose-500',    icon: HiTag },
  scroll:         { label: 'Scroll',          color: 'bg-teal-50 text-teal-700 border-teal-200',     dot: 'bg-teal-500',    icon: HiTrendingUp },
  time_on_page:   { label: 'Time on Page',    color: 'bg-sky-50 text-sky-700 border-sky-200',        dot: 'bg-sky-500',     icon: HiClock },
  dwell_time:     { label: 'Dwell Time',      color: 'bg-sky-50 text-sky-700 border-sky-200',        dot: 'bg-sky-500',     icon: HiClock },
  exit:           { label: 'Exit',            color: 'bg-red-50 text-red-600 border-red-200',        dot: 'bg-red-400',     icon: HiX },
  session_end:    { label: 'Session End',     color: 'bg-gray-50 text-gray-600 border-gray-200',     dot: 'bg-gray-400',    icon: HiTag },
  add_to_cart:    { label: 'Add to Cart',     color: 'bg-orange-50 text-orange-700 border-orange-200', dot: 'bg-orange-500', icon: HiTag },
  wishlist:       { label: 'Wishlist',        color: 'bg-pink-50 text-pink-700 border-pink-200',     dot: 'bg-pink-500',    icon: HiTag },
  repeat_visit:   { label: 'Repeat Visit',    color: 'bg-violet-50 text-violet-700 border-violet-200', dot: 'bg-violet-500', icon: HiEye },
  category_switch:{ label: 'Category Switch', color: 'bg-cyan-50 text-cyan-700 border-cyan-200',    dot: 'bg-cyan-500',    icon: HiFilter },
}

const getBadge = (type: string, meta?: any) => {
  if (meta?.action === 're_enroll' || meta?.action === 're-enroll') {
    return EVENT_CONFIG['re_enroll']
  }
  return EVENT_CONFIG[type] ?? {
    label: type.replace(/_/g, ' '),
    color: 'bg-gray-50 text-gray-700 border-gray-200',
    dot: 'bg-gray-400',
    icon: HiTag,
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────
const getDwellTime = (evt: UserEvent): number | null => {
  // dwell_time might be top-level or inside metadata
  if (evt.dwell_time != null) return Math.round(evt.dwell_time)
  const meta = evt.metadata as any
  if (meta?.dwell_time != null) return Math.round(Number(meta.dwell_time))
  return null
}

const getDetails = (evt: UserEvent, productsMap: Map<string, Product>): React.ReactNode => {
  const meta = evt.metadata as any
  const titleFromMeta = meta?.course_title || meta?.title

  if (evt.search_query)
    return <span className="font-medium text-gray-800">🔍 "{evt.search_query}"</span>

  // Try looking up course title from productsMap or metadata
  const productObj = evt.product_id ? productsMap.get(evt.product_id) : null
  const displayTitle = titleFromMeta || productObj?.title

  if (displayTitle) {
    return (
      <span className="font-semibold text-primary-900 bg-primary-50 px-2.5 py-1 rounded-lg border border-primary-100 text-xs inline-flex items-center gap-1">
        📚 {displayTitle}
      </span>
    )
  }

  if (evt.product_id)
    return (
      <span className="font-mono text-xs text-primary-600 bg-primary-50 px-2 py-0.5 rounded border border-primary-100">
        Product: {evt.product_id.substring(0, 8)}…
      </span>
    )

  if (evt.event_type === 'scroll' && meta?.scroll_depth != null)
    return (
      <span className="inline-flex items-center gap-2">
        <span className="text-gray-600">Scroll depth:</span>
        <span className="font-semibold text-teal-700">{meta.scroll_depth}%</span>
        {meta?.page_url && <span className="text-gray-400 text-xs font-mono">{meta.page_url}</span>}
      </span>
    )

  if ((evt.event_type === 'time_on_page' || evt.event_type === 'dwell_time') && meta?.page_url) {
    const courseMatch = meta.page_url.match(/\/courses\/([a-f0-9-]{36})/)
    if (courseMatch) {
      const prod = productsMap.get(courseMatch[1])
      if (prod) {
        return (
          <span className="font-medium text-gray-800 text-xs">
            Course Page: <span className="font-semibold text-primary-700">{prod.title}</span>
          </span>
        )
      }
    }
    return (
      <span className="inline-flex items-center gap-2">
        <span className="font-mono text-xs text-gray-500">{meta.page_url}</span>
      </span>
    )
  }

  if (meta?.page_url) {
    const courseMatch = meta.page_url.match(/\/courses\/([a-f0-9-]{36})/)
    if (courseMatch) {
      const prod = productsMap.get(courseMatch[1])
      if (prod) {
        return (
          <span className="font-medium text-gray-800 text-xs">
            Course Page: <span className="font-semibold text-primary-700">{prod.title}</span>
          </span>
        )
      }
    }
    return <span className="font-mono text-xs text-gray-500">{meta.page_url}</span>
  }

  if (meta?.category)
    return <span className="text-gray-700 font-medium">{meta.category}</span>

  return <span className="text-gray-400 text-xs italic">—</span>
}

// ── Breakdown bar ─────────────────────────────────────────────────────────────
const BreakdownBar = ({ label, count, total, dot }: { label: string; count: number; total: number; dot: string }) => {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="flex items-center gap-3">
      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dot}`} />
      <span className="text-xs text-gray-600 w-28 truncate">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full ${dot} opacity-70 transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-gray-700 w-8 text-right">{count}</span>
      <span className="text-xs text-gray-400 w-8 text-right">{pct}%</span>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export const ActivityPage = () => {
  const [events, setEvents] = useState<UserEvent[]>([])
  const [hashInfo, setHashInfo] = useState<EventHashResponse | null>(null)
  const [productsMap, setProductsMap] = useState<Map<string, Product>>(new Map())
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [filterType, setFilterType] = useState<string>('all')
  const [showFilterMenu, setShowFilterMenu] = useState(false)
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date())

  const fetchActivity = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    else setRefreshing(true)
    try {
      const [eventsData, hashData, productsData] = await Promise.all([
        getMyEvents(100),
        getMyEventHash(),
        getProducts().catch(() => []),
      ])
      setEvents(eventsData || [])
      setHashInfo(hashData)
      if (productsData && productsData.length > 0) {
        setProductsMap(new Map(productsData.map(p => [p.id, p])))
      }
      setLastRefreshed(new Date())
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { fetchActivity() }, [fetchActivity])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => fetchActivity(true), 30000)
    return () => clearInterval(interval)
  }, [fetchActivity])

  // ── Derived stats ─────────────────────────────────────────────────────────
  const totalEvents = hashInfo?.event_count ?? events.length

  const typeCounts = events.reduce<Record<string, number>>((acc, e) => {
    acc[e.event_type] = (acc[e.event_type] ?? 0) + 1
    return acc
  }, {})

  const topTypes = Object.entries(typeCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6)

  const activeEnrolledCount = (() => {
    const courseState = new Map<string, string>() // course_key -> latest event_type
    for (const e of events) {
      const meta = (e.metadata || (e as any).event_metadata || {})
      const key = e.product_id || meta.course_title || meta.title
      const evtType = String(e.event_type || '').toLowerCase()
      if (key && (evtType === 'enroll' || evtType === 'enrollment' || evtType === 'unenroll' || evtType === 'drop_course')) {
        if (!courseState.has(key)) {
          courseState.set(key, evtType)
        }
      }
    }
    let count = 0
    for (const type of courseState.values()) {
      if (type === 'enroll' || type === 'enrollment') {
        count++
      }
    }
    return count
  })()

  const uniqueCoursesViewedCount = new Set(
    events
      .filter(e => e.event_type === 'view_product')
      .map(e => {
        const meta = (e.metadata || (e as any).event_metadata || {})
        return e.product_id || meta.course_title || meta.title
      })
      .filter(Boolean)
  ).size

  const enrollCount   = activeEnrolledCount
  const searchCount   = typeCounts['search'] ?? 0
  const viewCount     = typeCounts['view_product'] ?? 0
  const avgDwell      = (() => {
    const dwells = events.map(getDwellTime).filter((d): d is number => d !== null)
    return dwells.length ? Math.round(dwells.reduce((a, b) => a + b, 0) / dwells.length) : null
  })()

  // ── Filtered events ───────────────────────────────────────────────────────
  const filtered = filterType === 'all'
    ? events
    : events.filter(e => e.event_type === filterType)

  const uniqueTypes = Array.from(new Set(events.map(e => e.event_type))).sort()

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

        {/* ── Header ── */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
              <HiLightningBolt className="w-8 h-8 text-amber-500" />
              Your Learning Activity
            </h1>
            <p className="text-gray-500 mt-1 text-sm">
              Real-time behavioral log · SmartReco uses this to personalize your recommendations
            </p>
          </div>
          <button
            onClick={() => fetchActivity(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50 shadow-sm transition-all disabled:opacity-50"
          >
            <HiRefresh className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* ── Top metric cards ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total Events',   value: totalEvents,                        sub: 'recorded in database',     color: 'text-primary-700' },
            { label: 'Course Views',   value: viewCount,                          sub: `${uniqueCoursesViewedCount} unique course${uniqueCoursesViewedCount === 1 ? '' : 's'} viewed`, color: 'text-blue-700' },
            { label: 'Active Enrollments', value: enrollCount,                        sub: 'active course count',      color: 'text-emerald-700' },
            { label: 'Avg Dwell Time', value: avgDwell != null ? `${avgDwell}s` : '—', sub: 'per session page', color: 'text-sky-700' },
          ].map(card => (
            <div key={card.label} className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">{card.label}</div>
              <div className={`text-3xl font-extrabold ${card.color}`}>{card.value}</div>
              <div className="text-xs text-gray-400 mt-1">{card.sub}</div>
            </div>
          ))}
        </div>

        {/* ── Two-column layout: breakdown + hash ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* Event type breakdown */}
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-900">Event Type Breakdown</h3>
              <span className="text-xs text-gray-400">{topTypes.length} types tracked</span>
            </div>
            {loading ? (
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-5 bg-gray-100 rounded animate-pulse" />
                ))}
              </div>
            ) : topTypes.length === 0 ? (
              <p className="text-gray-400 text-sm">No events yet.</p>
            ) : (
              <div className="space-y-3">
                {topTypes.map(([type, count]) => {
                  const badge = getBadge(type)
                  return (
                    <BreakdownBar
                      key={type}
                      label={badge.label}
                      count={count}
                      total={events.length}
                      dot={badge.dot}
                    />
                  )
                })}
              </div>
            )}
          </div>

          {/* AI status + hash card */}
          <div className="space-y-4">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
              <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">AI Engine Status</div>
              <div className="flex items-center gap-2 mb-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
                </span>
                <span className="text-sm font-bold text-gray-900">Active Real-Time Tracking</span>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">
                Monitors your browsing and course views in real time. Refreshes activity stream every 30 seconds.
              </p>
              <div className="text-[11px] text-gray-400 mt-2 font-medium">
                Last refreshed: {lastRefreshed.toLocaleTimeString()}
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Behavioral Hash</div>
                <span className="text-[10px] font-bold px-2 py-0.5 bg-primary-50 text-primary-700 rounded-md border border-primary-100">
                  Cache Key
                </span>
              </div>
              <div className="font-mono text-xs text-primary-700 bg-primary-50 rounded-xl px-3 py-2 break-all border border-primary-100 shadow-2xs">
                {hashInfo?.event_hash || '—'}
              </div>
              <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                MD5 digital signature of your last 20 behavioral events. Triggers automatic cache invalidation when your learning interest shifts.
              </p>
              {searchCount > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="text-xs text-gray-600 font-medium">
                    🔍 <span className="font-bold text-gray-900">{searchCount}</span> searches tracked
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Event stream table ── */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-5 border-b border-gray-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-gray-900">Recent Event Stream</h3>
              <p className="text-xs text-gray-400 mt-0.5">Last 100 events · most recent first</p>
            </div>

            {/* Filter dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowFilterMenu(v => !v)}
                className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
              >
                <HiFilter className="w-4 h-4" />
                {filterType === 'all' ? 'All types' : getBadge(filterType).label}
                <HiChevronDown className="w-4 h-4" />
              </button>
              {showFilterMenu && (
                <div className="absolute right-0 mt-1 w-52 bg-white border border-gray-100 rounded-xl shadow-lg z-10 py-1 max-h-64 overflow-y-auto">
                  <button
                    onClick={() => { setFilterType('all'); setShowFilterMenu(false) }}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${filterType === 'all' ? 'font-semibold text-primary-700' : 'text-gray-700'}`}
                  >
                    All types ({events.length})
                  </button>
                  {uniqueTypes.map(type => (
                    <button
                      key={type}
                      onClick={() => { setFilterType(type); setShowFilterMenu(false) }}
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex justify-between ${filterType === type ? 'font-semibold text-primary-700' : 'text-gray-700'}`}
                    >
                      <span>{getBadge(type).label}</span>
                      <span className="text-gray-400">{typeCounts[type]}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">Loading activity logs…</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-12 text-center">
              <HiLightningBolt className="w-12 h-12 text-gray-200 mx-auto mb-3" />
              <h4 className="text-base font-bold text-gray-700">No events logged yet</h4>
              <p className="text-xs text-gray-400 mt-1">Browse courses or enroll to start building your behavioral profile.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-100">
                    <th className="px-5 py-3 w-40">Event Type</th>
                    <th className="px-5 py-3">Details / Target</th>
                    <th className="px-5 py-3 w-32">Dwell Time</th>
                    <th className="px-5 py-3 w-44">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {filtered.map((evt) => {
                    const badge  = getBadge(evt.event_type, evt.metadata || (evt as any).event_metadata)
                    const Icon   = badge.icon
                    const dwell  = getDwellTime(evt)
                    const details = getDetails(evt, productsMap)

                    return (
                      <tr key={evt.id} className="hover:bg-gray-50/70 transition-colors group">
                        <td className="px-5 py-3.5">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${badge.color}`}>
                            <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                            {badge.label}
                          </span>
                        </td>

                        <td className="px-5 py-3.5 max-w-xs">
                          <div className="truncate">{details}</div>
                        </td>

                        <td className="px-5 py-3.5">
                          {dwell != null ? (
                            <span className="inline-flex items-center gap-1 text-xs font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded-lg border border-sky-100 font-semibold shadow-2xs">
                              <HiClock className="w-3 h-3 text-sky-600" />
                              {dwell}s
                            </span>
                          ) : (
                            <span className="text-gray-400 text-xs font-medium italic">Instant Action</span>
                          )}
                        </td>

                        <td className="px-5 py-3.5 text-xs text-gray-400">
                          {(evt.timestamp ? new Date(evt.timestamp.endsWith('Z') || evt.timestamp.includes('+') ? evt.timestamp : evt.timestamp + 'Z') : new Date()).toLocaleString(undefined, {
                            month: 'short', day: 'numeric',
                            hour: '2-digit', minute: '2-digit', second: '2-digit'
                          })}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

              {/* Footer count */}
              <div className="px-5 py-3 border-t border-gray-100 text-xs text-gray-400 flex justify-between">
                <span>Showing {filtered.length} of {events.length} events</span>
                {filterType !== 'all' && (
                  <button
                    onClick={() => setFilterType('all')}
                    className="text-primary-600 hover:underline font-medium"
                  >
                    Clear filter
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

      </main>
    </div>
  )
}

export default ActivityPage
