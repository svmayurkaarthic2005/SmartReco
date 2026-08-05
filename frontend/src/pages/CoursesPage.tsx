/**
 * Courses Catalog Page with React Icons
 */

import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/layout/Navbar'
import { getProducts, Product } from '../api/products'
import { trackEvent } from '../api/events'
import { useAuthStore } from '../store/authStore'
import { 
  HiBookOpen, 
  HiSearch, 
  HiFilter, 
  HiArrowRight, 
  HiRefresh 
} from 'react-icons/hi'

export const CoursesPage = () => {
  const { user } = useAuthStore()
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedCategory, setSelectedCategory] = useState<string>('All')
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('All')

  useEffect(() => {
    const fetchCourses = async () => {
      setLoading(true)
      const data = await getProducts()
      setProducts(data)
      setLoading(false)
    }
    fetchCourses()
  }, [])

  // Categories list
  const categories = useMemo(() => {
    const cats = new Set(products.map((p) => p.category))
    return ['All', ...Array.from(cats)]
  }, [products])

  // Filtered products
  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      const matchesSearch =
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()))

      const matchesCategory = selectedCategory === 'All' || p.category === selectedCategory
      const matchesDifficulty =
        selectedDifficulty === 'All' || p.difficulty_level.toUpperCase() === selectedDifficulty.toUpperCase()

      return matchesSearch && matchesCategory && matchesDifficulty
    })
  }, [products, searchQuery, selectedCategory, selectedDifficulty])

  const handleCourseClick = (product: Product) => {
    if (user) {
      trackEvent({
        user_id: user.id,
        session_id: 'session-' + Date.now(),
        event_type: 'view_product',
        product_id: product.id,
        event_metadata: { title: product.title, category: product.category, price: product.price }
      })
    }
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim() && user) {
      trackEvent({
        user_id: user.id,
        session_id: 'session-' + Date.now(),
        event_type: 'search',
        search_query: searchQuery,
      })
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
            <HiBookOpen className="w-8 h-8 text-primary-600" /> Course Catalog
          </h1>
          <p className="text-gray-600 mt-1">
            Explore industry-leading courses designed to help you master modern tech skills.
          </p>
        </div>

        {/* Search & Filter Controls */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-8 space-y-4">
          
          {/* Search bar */}
          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              placeholder="Search courses by keyword, topic, or technology (e.g. React, Python, AWS)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            />
            <HiSearch className="w-5 h-5 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
          </form>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider mr-2 shrink-0 flex items-center gap-1">
              <HiFilter className="w-3.5 h-3.5" /> Category:
            </span>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  selectedCategory === cat
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Difficulty Filter */}
          <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider mr-2">Difficulty:</span>
            {['All', 'BEGINNER', 'INTERMEDIATE', 'ADVANCED'].map((level) => (
              <button
                key={level}
                onClick={() => setSelectedDifficulty(level)}
                className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-colors ${
                  selectedDifficulty === level
                    ? 'bg-gray-900 text-white font-semibold'
                    : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
                }`}
              >
                {level.toLowerCase()}
              </button>
            ))}
          </div>

        </div>

        {/* Loading */}
        {loading && (
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mx-auto mb-3"></div>
            <p className="text-gray-500 text-sm">Loading course catalog...</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && filteredProducts.length === 0 && (
          <div className="bg-white rounded-2xl p-12 text-center border border-gray-100 shadow-sm">
            <HiSearch className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-gray-800">No courses match your criteria</h3>
            <p className="text-gray-500 text-sm mt-1">Try clearing your search query or filters.</p>
            <button
              onClick={() => { setSearchQuery(''); setSelectedCategory('All'); setSelectedDifficulty('All') }}
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 transition-colors inline-flex items-center gap-2"
            >
              <HiRefresh className="w-4 h-4" /> Reset Filters
            </button>
          </div>
        )}

        {/* Courses Grid */}
        {!loading && filteredProducts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProducts.map((product) => (
              <div
                key={product.id}
                className="bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all border border-gray-100 p-6 flex flex-col justify-between group"
              >
                <div>
                  {/* Category & Difficulty Badge */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-semibold rounded-md border border-primary-100">
                      {product.category}
                    </span>
                    <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded capitalize">
                      {product.difficulty_level.toLowerCase()} • {product.duration_hours || 10}h
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-gray-900 group-hover:text-primary-600 transition-colors mb-2 line-clamp-2">
                    {product.title}
                  </h3>

                  <p className="text-gray-600 text-xs line-clamp-3 mb-4 leading-relaxed">
                    {product.description}
                  </p>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {product.tags.slice(0, 4).map((tag) => (
                      <span key={tag} className="text-[11px] bg-gray-50 text-gray-500 px-2 py-0.5 rounded border border-gray-200">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-100 flex items-center justify-between mt-2">
                  <div>
                    <div className="text-xl font-extrabold text-gray-900">${product.price}</div>
                    <div className="text-[11px] text-emerald-600 font-semibold">Self-paced learning</div>
                  </div>

                  <Link
                    to={`/courses/${product.id}`}
                    onClick={() => handleCourseClick(product)}
                    className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-semibold text-xs rounded-xl transition-colors shadow-sm inline-flex items-center gap-1"
                  >
                    View Details <HiArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

      </main>
    </div>
  )
}

export default CoursesPage
