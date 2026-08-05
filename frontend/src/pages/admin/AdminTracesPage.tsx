/**
 * Admin Traces Page
 * LangSmith trace viewer with expandable details
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, ChevronDown, ChevronRight, Clock, Zap } from 'lucide-react'
import { getLangSmithTraces } from '../../api/admin'

const AdminTracesPage = () => {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [expandedTrace, setExpandedTrace] = useState<string | null>(null)

  // Fetch traces with auto-refresh every 30 seconds
  const { data: traces, isLoading } = useQuery({
    queryKey: ['admin', 'traces', statusFilter],
    queryFn: () => getLangSmithTraces({ 
      limit: 100,
      status: statusFilter || undefined 
    }),
    refetchInterval: 30000, // 30 seconds
  })

  // Filter traces
  const filteredTraces = traces?.filter((trace) => {
    const matchesSearch = trace.name.toLowerCase().includes(search.toLowerCase())
    const matchesStatus = !statusFilter || trace.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const toggleExpand = (traceId: string) => {
    setExpandedTrace(expandedTrace === traceId ? null : traceId)
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      success: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
    }
    return styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800'
  }

  const formatLatency = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">LangSmith Traces</h1>
          <p className="text-gray-600 mt-1">
            AI workflow execution logs (auto-refreshes every 30s)
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by run name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Statuses</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
            <option value="pending">Pending</option>
          </select>
        </div>
      </div>

      {/* Traces Table */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase w-8"></th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Run Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Latency</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Token Usage</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    Loading traces...
                  </td>
                </tr>
              ) : filteredTraces?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No traces found
                  </td>
                </tr>
              ) : (
                <>
                  {filteredTraces?.map((trace) => (
                    <>
                      {/* Main row */}
                      <tr 
                        key={trace.run_id} 
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => toggleExpand(trace.run_id)}
                      >
                        <td className="px-6 py-4">
                          {expandedTrace === trace.run_id ? (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronRight className="w-5 h-5 text-gray-400" />
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm font-medium text-gray-900">{trace.name}</div>
                          <div className="text-xs text-gray-500 font-mono">{trace.run_id}</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(trace.status)}`}>
                            {trace.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2 text-sm text-gray-900">
                            <Clock className="w-4 h-4 text-gray-400" />
                            {formatLatency(trace.latency_ms)}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2 text-sm text-gray-900">
                            <Zap className="w-4 h-4 text-gray-400" />
                            {trace.token_usage || 0}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {formatTimestamp(trace.timestamp)}
                        </td>
                      </tr>

                      {/* Expanded details row */}
                      {expandedTrace === trace.run_id && (
                        <tr>
                          <td colSpan={6} className="px-6 py-4 bg-gray-50">
                            <div className="space-y-4">
                              {/* Input */}
                              {trace.inputs && (
                                <div>
                                  <div className="text-sm font-semibold text-gray-700 mb-2">Input</div>
                                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                                    <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                                      {JSON.stringify(trace.inputs, null, 2)}
                                    </pre>
                                  </div>
                                </div>
                              )}

                              {/* Output */}
                              {trace.outputs && (
                                <div>
                                  <div className="text-sm font-semibold text-gray-700 mb-2">Output</div>
                                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                                    <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                                      {JSON.stringify(trace.outputs, null, 2)}
                                    </pre>
                                  </div>
                                </div>
                              )}

                              {/* Error */}
                              {trace.error && (
                                <div>
                                  <div className="text-sm font-semibold text-red-700 mb-2">Error</div>
                                  <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                                    <pre className="text-xs text-red-700 whitespace-pre-wrap font-mono">
                                      {trace.error}
                                    </pre>
                                  </div>
                                </div>
                              )}

                              {/* Metadata */}
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <div className="text-gray-500">Run Type</div>
                                  <div className="font-medium text-gray-900">{trace.run_type || 'N/A'}</div>
                                </div>
                                <div>
                                  <div className="text-gray-500">Total Cost</div>
                                  <div className="font-medium text-gray-900">
                                    {trace.total_cost ? `$${trace.total_cost.toFixed(4)}` : 'N/A'}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-gray-500">Prompt Tokens</div>
                                  <div className="font-medium text-gray-900">{trace.prompt_tokens || 0}</div>
                                </div>
                                <div>
                                  <div className="text-gray-500">Completion Tokens</div>
                                  <div className="font-medium text-gray-900">{trace.completion_tokens || 0}</div>
                                </div>
                              </div>

                              {/* LangSmith link */}
                              {trace.url && (
                                <div>
                                  <a
                                    href={trace.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                                  >
                                    View in LangSmith →
                                  </a>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AdminTracesPage
