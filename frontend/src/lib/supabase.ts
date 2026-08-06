import { createClient } from '@supabase/supabase-js'

// @supabase/supabase-js v2.112.1 supports sb_publishable_ key format
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://lrjxlsvgsfakpxwkibpk.supabase.co'
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_2ZPlTkpu6k0OM_mtFsv3yw_nLuiwcjT'

export const supabase = createClient(supabaseUrl, supabaseKey)
