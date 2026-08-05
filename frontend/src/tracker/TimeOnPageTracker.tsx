/**
 * Time on Page Tracker Component
 * Tracks total dwell time on current page
 */

import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { useTracker } from './useTracker'

export const TimeOnPageTracker = () => {
  const { trackEvent } = useTracker()
  const location = useLocation()
  const startTimeRef = useRef<number>(Date.now())
  const isVisibleRef = useRef<boolean>(true)

  useEffect(() => {
    // Reset start time on route change
    startTimeRef.current = Date.now()

    // Track page visibility
    const handleVisibilityChange = () => {
      isVisibleRef.current = !document.hidden
    }

    // Send dwell time on unmount
    const sendDwellTime = () => {
      if (isVisibleRef.current) {
        const dwellTime = Math.round((Date.now() - startTimeRef.current) / 1000) // seconds
        
        if (dwellTime >= 1) { // Track dwell time >= 1 second
          const courseMatch = location.pathname.match(/\/courses\/([a-f0-9-]{36})/)
          const productId = courseMatch ? courseMatch[1] : undefined

          trackEvent({
            event_type: 'time_on_page',
            dwell_time: dwellTime,
            product_id: productId,
            metadata: {
              dwell_time: dwellTime,
              page_url: location.pathname,
            },
          })
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    // Send on route change or page unload
    return () => {
      sendDwellTime()
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [location.pathname, trackEvent])

  return null
}
