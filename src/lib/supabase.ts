import { createClient } from '@supabase/supabase-js';

// SUPABASE PLACEHOLDER: Replace with your Supabase Project URL
// Find this in: Supabase Dashboard → Project Settings → API → Project URL
const supabaseUrl = 'YOUR_SUPABASE_PROJECT_URL';

// SUPABASE PLACEHOLDER: Replace with your Supabase Anon/Public Key
// Find this in: Supabase Dashboard → Project Settings → API → Project API keys → anon public
const supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
