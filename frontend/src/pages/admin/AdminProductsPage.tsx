/**
 * Admin Products Page
 * CRUD operations for products with drawer form
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Package, Plus, Search, Edit, Trash2, RefreshCw, X } from 'lucide-react'
import { getProducts, createProduct, updateProduct, deleteProduct, reembedProduct, retryFailedEmbeddings } from '../../api/admin'
import { useToast } from '../../context/ToastContext'
import { Product, CreateProductPayload } from '../../types/admin'

const AdminProductsPage = () => {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [difficultyFilter, setDifficultyFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  // Fetch products
  const { data: productsData, isLoading } = useQuery({
    queryKey: ['admin', 'products', search, categoryFilter, difficultyFilter, statusFilter],
    queryFn: () => getProducts({
      search,
      category: categoryFilter || undefined,
      difficulty: difficultyFilter || undefined,
      embedding_status: statusFilter || undefined,
    }),
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'products'] })
      showToast('success', 'Product created successfully')
      setIsDrawerOpen(false)
    },
    onError: () => {
      showToast('error', 'Failed to create product')
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateProductPayload> }) => 
      updateProduct(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'products'] })
      showToast('success', 'Product updated successfully')
      setIsDrawerOpen(false)
      setEditingProduct(null)
    },
    onError: () => {
      showToast('error', 'Failed to update product')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'products'] })
      showToast('success', 'Product deleted successfully')
      setDeleteConfirm(null)
    },
    onError: () => {
      showToast('error', 'Failed to delete product')
    },
  })

  // Re-embed mutation
  const reembedMutation = useMutation({
    mutationFn: reembedProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'products'] })
      showToast('success', 'Re-embedding started')
    },
    onError: () => {
      showToast('error', 'Failed to start re-embedding')
    },
  })

  // Retry failed embeddings
  const retryMutation = useMutation({
    mutationFn: retryFailedEmbeddings,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'products'] })
      showToast('success', `Retrying ${data.count} failed embeddings`)
    },
    onError: () => {
      showToast('error', 'Failed to retry embeddings')
    },
  })

  const openDrawer = (product?: Product) => {
    if (product) {
      setEditingProduct(product)
    }
    setIsDrawerOpen(true)
  }

  const closeDrawer = () => {
    setIsDrawerOpen(false)
    setEditingProduct(null)
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      indexed: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
    }
    return styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Products Management</h1>
          <p className="text-gray-600 mt-1">Manage course catalog and embeddings</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => retryMutation.mutate()}
            disabled={retryMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${retryMutation.isPending ? 'animate-spin' : ''}`} />
            Retry Failed
          </button>
          <button
            onClick={() => openDrawer()}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Plus className="w-4 h-4" />
            Add Product
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search products..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Category filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Categories</option>
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="data_science">Data Science</option>
            <option value="web_development">Web Development</option>
          </select>

          {/* Difficulty filter */}
          <select
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Difficulties</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Statuses</option>
            <option value="indexed">Indexed</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Difficulty</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    Loading products...
                  </td>
                </tr>
              ) : productsData?.products.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No products found
                  </td>
                </tr>
              ) : (
                productsData?.products.map((product) => (
                  <tr key={product.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <Package className="w-5 h-5 text-gray-400 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{product.title}</div>
                          <div className="text-sm text-gray-500">{product.duration_hours}h duration</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">{product.category}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {product.difficulty}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">${product.price}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(product.embedding_status)}`}>
                        {product.embedding_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => openDrawer(product)}
                          className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => reembedMutation.mutate(product.id)}
                          className="p-1 text-green-600 hover:bg-green-50 rounded"
                          title="Re-embed"
                          disabled={reembedMutation.isPending}
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setDeleteConfirm(product.id)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Product Form Drawer */}
      {isDrawerOpen && (
        <ProductDrawer
          product={editingProduct}
          onClose={closeDrawer}
          onSubmit={(data) => {
            if (editingProduct) {
              updateMutation.mutate({ id: editingProduct.id, data })
            } else {
              createMutation.mutate(data)
            }
          }}
          isSubmitting={createMutation.isPending || updateMutation.isPending}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <DeleteModal
          onConfirm={() => deleteMutation.mutate(deleteConfirm)}
          onCancel={() => setDeleteConfirm(null)}
          isDeleting={deleteMutation.isPending}
        />
      )}
    </div>
  )
}

// Product Drawer Component
interface ProductDrawerProps {
  product: Product | null
  onClose: () => void
  onSubmit: (data: CreateProductPayload) => void
  isSubmitting: boolean
}

const ProductDrawer = ({ product, onClose, onSubmit, isSubmitting }: ProductDrawerProps) => {
  const [formData, setFormData] = useState<CreateProductPayload>({
    title: product?.title || '',
    description: product?.description || '',
    category: product?.category || '',
    difficulty: product?.difficulty || 'beginner',
    price: product?.price || 0,
    duration_hours: product?.duration_hours || 0,
    tags: product?.tags || [],
  })

  const handleSubmit = () => {
    onSubmit(formData)
  }

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={onClose}></div>
      
      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-full max-w-2xl bg-white shadow-xl z-50 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {product ? 'Edit Product' : 'Add Product'}
            </h2>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Form */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="Course title"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="Course description"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Difficulty</label>
                <select
                  value={formData.difficulty}
                  onChange={(e) => setFormData({ ...formData, difficulty: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price ($)</label>
                <input
                  type="number"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duration (hours)</label>
                <input
                  type="number"
                  value={formData.duration_hours}
                  onChange={(e) => setFormData({ ...formData, duration_hours: parseFloat(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tags (comma-separated)</label>
              <input
                type="text"
                value={formData.tags.join(', ')}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value.split(',').map(t => t.trim()) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="python, programming, beginner"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={onClose}
              className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex-1 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : product ? 'Update' : 'Create'}
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

// Delete Modal
interface DeleteModalProps {
  onConfirm: () => void
  onCancel: () => void
  isDeleting: boolean
}

const DeleteModal = ({ onConfirm, onCancel, isDeleting }: DeleteModalProps) => (
  <>
    <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={onCancel}></div>
    <div className="fixed inset-0 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 max-w-md">
        <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Product?</h3>
        <p className="text-gray-600 mb-6">This action cannot be undone.</p>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  </>
)

export default AdminProductsPage
