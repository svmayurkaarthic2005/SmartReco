/**
 * Admin Dashboard Page
 * Overview with stats, charts, and recent data
 */

import { useQuery } from '@tanstack/react-query'
import { Users, Activity, Brain, AlertTriangle, Database, TrendingUp } from 'lucide-react'
import { getStats, getPersonaDistribution, getEventVolume, getRecentRecommendations } from '../../api/admin'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

const AdminDashboardPage = () => {
  // Fetch data
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: getStats,
    refetchInterval: 30000, // Refresh every 30s
  })

  const { data: personaData } = useQuery({
    queryKey: ['admin', 'persona-distribution'],
    queryFn: getPersonaDistribution,
  })

  const { data: eventData } = useQuery({
    queryKey: ['admin', 'event-volume'],
    queryFn: () => getEventVolume(24),
  })

  const { data: recentRecs } = useQuery({
    queryKey: ['admin', 'recent-recommendations'],
    queryFn: () => getRecentRecommendations(10),
  })

  // Persona colors
  const PERSONA_COLORS: Record<string, string> = {
    explorer: '#6366f1',
    focused_builder: '#10b981',
    career_switcher: '#f59e0b',
    price_sensitive: '#f97316',
    overwhelmed_learner: '#ec4899',
    drop_off_risk: '#dc2626',
  }

  // Transform persona data for chart
  const personaChartData = personaData
    ? Object.entries(personaData).map(([name, value]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value,
      }))
    : []

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          icon={Users}
          label="Total Users"
          value={stats?.total_users || 0}
          color="bg-blue-500"
        />
        <StatCard
          icon={Activity}
          label="Events (7d)"
          value={stats?.total_events_7d || 0}
          color="bg-green-500"
        />
        <StatCard
          icon={Brain}
          label="Recommendations"
          value={stats?.total_recommendations || 0}
          color="bg-purple-500"
        />
        <StatCard
          icon={TrendingUp}
          label="AI Calls"
          value={stats?.ai_calls || 0}
          color="bg-indigo-500"
        />
        <StatCard
          icon={AlertTriangle}
          label="At Risk Users"
          value={stats?.drop_off_risk_count || 0}
          color="bg-red-500"
          alert={stats && stats.drop_off_risk_count > 0}
        />
        <StatCard
          icon={Database}
          label="Embed Failures"
          value={stats?.embedding_failures || 0}
          color="bg-orange-500"
          alert={stats && stats.embedding_failures > 0}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Persona Distribution */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Persona Distribution</h3>
          {personaChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={personaChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }: { name?: string; percent?: number }) => `${name || ''} ${((percent || 0) * 100).toFixed(0)}%`}
                >
                  {personaChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PERSONA_COLORS[entry.name.toLowerCase().replace(/ /g, '_')] || '#6366f1'} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </div>

        {/* Event Volume */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Event Volume (24h)</h3>
          {eventData && eventData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={eventData}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="count" stroke="#6366f1" fillOpacity={1} fill="url(#colorCount)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </div>
      </div>

      {/* Recent Recommendations Table */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">Recent Recommendations</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Persona</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Products</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Generated</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentRecs?.map((rec) => (
                <tr key={rec.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {rec.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full`}
                      style={{ 
                        backgroundColor: `${PERSONA_COLORS[rec.persona] || '#6366f1'}20`,
                        color: PERSONA_COLORS[rec.persona] || '#6366f1'
                      }}
                    >
                      {rec.persona.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full" 
                          style={{ width: `${rec.confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-700">{(rec.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {rec.product_count} courses
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(rec.generated_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// Stat Card Component
interface StatCardProps {
  icon: React.ElementType
  label: string
  value: number
  color: string
  alert?: boolean
}

const StatCard = ({ icon: Icon, label, value, color, alert }: StatCardProps) => (
  <div className="bg-white rounded-xl shadow-lg p-6 relative overflow-hidden">
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-600 mb-1">{label}</p>
        <p className="text-3xl font-bold text-gray-900">{value.toLocaleString()}</p>
      </div>
      <div className={`${color} p-3 rounded-lg`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
    </div>
    {alert && (
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-red-500"></div>
    )}
  </div>
)

export default AdminDashboardPage
