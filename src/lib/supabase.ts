import { createClient } from '@supabase/supabase-js';

// SUPABASE PLACEHOLDER: Replace with your Supabase Project URL
// Find this in: Supabase Dashboard → Project Settings → API → Project URL
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'YOUR_SUPABASE_PROJECT_URL';

// SUPABASE PLACEHOLDER: Replace with your Supabase Anon/Public Key
// Find this in: Supabase Dashboard → Project Settings → API → Project API keys → anon public
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'YOUR_SUPABASE_ANON_KEY';

// Check if credentials are configured
const isConfigured = supabaseUrl !== 'YOUR_SUPABASE_PROJECT_URL' && 
                     supabaseAnonKey !== 'YOUR_SUPABASE_ANON_KEY' &&
                     supabaseUrl.startsWith('http');

export const supabase = isConfigured 
  ? createClient(supabaseUrl, supabaseAnonKey)
  : createClient('https://placeholder.supabase.co', 'placeholder-key');
