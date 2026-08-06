import { createClient } from '@supabase/supabase-js'

// Use the JWT anon key (required by @supabase/supabase-js SDK)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://lrjxlsvgsfakpxwkibpk.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY ||
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxyanhsc3Znc2Zha3B4d2tpYnBrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU5OTcxODEsImV4cCI6MjEwMTU3MzE4MX0.T66IV8bTTOUmfCKEfg8MEO6Vob1m54D-j-ztcG2MTNU'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
