/**
 * Products API endpoints
 */

import { apiClient } from './client'

export interface Product {
  id: string
  title: string
  description: string
  category: string
  price: number
  difficulty_level: string
  duration_hours: number
  tags: string[]
  embedding_status: string
  created_at: string
}

/**
 * Get products (search / filter)
 */
export const getProducts = async (params?: { category?: string; difficulty?: string; limit?: number }): Promise<Product[]> => {
  // Fetch products from public /products endpoint
  // Short 8s timeout: this is a simple DB query, not an LLM call.
  // If backend is busy with recommendations, fail fast and use defaults.
  try {
    const response = await apiClient.get<Product[]>('/products', {
      params: { limit: params?.limit ?? 50, ...params },
      timeout: 8000,
    })
    if (response.data && response.data.length > 0) {
      return response.data
    }
  } catch (err) {
    console.warn('Failed to fetch products from backend, using default courses:', err)
  }
  return [
    {
      id: '11111111-1111-1111-1111-111111111111',
      title: 'Python for Beginners & Data Science',
      description: 'Master Python fundamentals, data structures, pandas, and basic machine learning.',
      category: 'Data Science',
      price: 49.99,
      difficulty_level: 'BEGINNER',
      duration_hours: 15.5,
      tags: ['python', 'data-science', 'pandas', 'coding'],
      embedding_status: 'INDEXED',
      created_at: new Date().toISOString()
    },
    {
      id: '22222222-2222-2222-2222-222222222222',
      title: 'Full-Stack Web Development with React & Node',
      description: 'Build modern responsive web applications with TypeScript, React, Tailwind, and Node.js.',
      category: 'Web Development',
      price: 89.99,
      difficulty_level: 'INTERMEDIATE',
      duration_hours: 32.0,
      tags: ['react', 'typescript', 'web-dev', 'frontend'],
      embedding_status: 'INDEXED',
      created_at: new Date().toISOString()
    },
    {
      id: '33333333-3333-3333-3333-333333333333',
      title: 'Deep Learning & Neural Networks Masterclass',
      description: 'Explore PyTorch, convolutional networks, transformers, and generative AI models.',
      category: 'Machine Learning',
      price: 119.99,
      difficulty_level: 'ADVANCED',
      duration_hours: 45.0,
      tags: ['ai', 'deep-learning', 'pytorch', 'transformers'],
      embedding_status: 'INDEXED',
      created_at: new Date().toISOString()
    },
    {
      id: '44444444-4444-4444-4444-444444444444',
      title: 'Cloud Architecture & AWS Solutions Architect',
      description: 'Design scalable, fault-tolerant cloud systems using AWS services, Docker, and Kubernetes.',
      category: 'Cloud & DevOps',
      price: 79.99,
      difficulty_level: 'INTERMEDIATE',
      duration_hours: 28.0,
      tags: ['aws', 'cloud', 'docker', 'devops'],
      embedding_status: 'INDEXED',
      created_at: new Date().toISOString()
    },
    {
      id: '55555555-5555-5555-5555-555555555555',
      title: 'SQL Database Design & High-Performance Querying',
      description: 'Learn relational database modeling, indexing, query optimization, and PostgreSQL internals.',
      category: 'Database',
      price: 39.99,
      difficulty_level: 'BEGINNER',
      duration_hours: 12.0,
      tags: ['sql', 'postgresql', 'database', 'backend'],
      embedding_status: 'INDEXED',
      created_at: new Date().toISOString()
    },
    {
      id: '66666666-6666-6666-6666-666666666666',
      title: 'UI/UX Design Systems & Figma Mastery',
      description: 'Design intuitive digital products with modern typography, layout grids, and interactive prototypes.',
      category: 'Design',
      price: 59.99,
      difficulty_level: 'BEGINNER',
      duration_hours: 18.0,
      tags: ['ui-ux', 'figma', 'design-systems', 'frontend'],
      embedding_status: 'INDEXED',
      created_at: new Date().toISOString()
    }
  ]
}
