/**
 * Event tracker hook
 * Buffers events and sends in batches to /events/batch endpoint
 */

import { useRef, useEffect, useCallback } from 'react'
import { apiClient } from '../api/client'
import { v4 as uuidv4 } from '../utils/uuid'

export interface EventPayload {
  event_type: string
  product_id?: string
  search_query?: string
  dwell_time?: number
  metadata?: Record<string, any>
}

const BUFFER_SIZE = 20
const FLUSH_INTERVAL = 10000 // 10 seconds

export const useTracker = () => {
  const eventBuffer = useRef<any[]>([])
  const sessionId = useRef<string>(uuidv4())
  const flushTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const flushBuffer = useCallback(async () => {
    if (eventBuffer.current.length === 0) return

    try {
      const events = [...eventBuffer.current]
      eventBuffer.current = []

      await apiClient.post('/events/batch', { events })
    } catch (error) {
      console.error('Failed to send events:', error)
      // Don't re-queue failed events to avoid infinite loop
    }
  }, [])

  const trackEvent = useCallback((payload: EventPayload) => {
    const event = {
      ...payload,
      session_id: sessionId.current,
      timestamp: new Date().toISOString(),
    }

    eventBuffer.current.push(event)

    // Flush if buffer full
    if (eventBuffer.current.length >= BUFFER_SIZE) {
      flushBuffer()
      
      // Clear existing timeout
      if (flushTimeoutRef.current) {
        clearTimeout(flushTimeoutRef.current)
        flushTimeoutRef.current = null
      }
    } else {
      // Reset flush timeout
      if (flushTimeoutRef.current) {
        clearTimeout(flushTimeoutRef.current)
      }
      
      flushTimeoutRef.current = setTimeout(() => {
        flushBuffer()
        flushTimeoutRef.current = null
      }, FLUSH_INTERVAL)
    }
  }, [flushBuffer])

  // Flush on unmount or beforeunload
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (eventBuffer.current.length > 0) {
        // Use sendBeacon for reliable delivery on page unload
        const blob = new Blob(
          [JSON.stringify({ events: eventBuffer.current })],
          { type: 'application/json' }
        )
        navigator.sendBeacon(
          `${apiClient.defaults.baseURL}/events/batch`,
          blob
        )
        eventBuffer.current = []
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)

    return () => {
      handleBeforeUnload()
      window.removeEventListener('beforeunload', handleBeforeUnload)
      
      if (flushTimeoutRef.current) {
        clearTimeout(flushTimeoutRef.current)
      }
    }
  }, [])

  // Periodic flush
  useEffect(() => {
    const interval = setInterval(() => {
      flushBuffer()
    }, FLUSH_INTERVAL)

    return () => clearInterval(interval)
  }, [flushBuffer])

  return { trackEvent, flushBuffer }
}
