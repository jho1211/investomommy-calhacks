import { createClient } from '@supabase/supabase-js';

// SUPABASE PLACEHOLDER: Replace with your Supabase Project URL
// Find this in: Supabase Dashboard → Project Settings → API → Project URL
const supabaseUrl = (import.meta as any).env?.VITE_SUPABASE_URL || 'YOUR_SUPABASE_PROJECT_URL';

// SUPABASE PLACEHOLDER: Replace with your Supabase Anon/Public Key
// Find this in: Supabase Dashboard → Project Settings → API → Project API keys → anon public
const supabaseAnonKey = (import.meta as any).env?.VITE_SUPABASE_ANON_KEY || 'YOUR_SUPABASE_ANON_KEY';

// Determine if configured with a valid URL
const hasValidUrl = typeof supabaseUrl === 'string' && /^https?:\/\//i.test(supabaseUrl);
const isConfigured = hasValidUrl &&
  supabaseUrl !== 'YOUR_SUPABASE_PROJECT_URL' &&
  supabaseAnonKey !== 'YOUR_SUPABASE_ANON_KEY';

let supabase: any;

if (isConfigured) {
  supabase = createClient(supabaseUrl, supabaseAnonKey);
} else {
  // Friendly no-op client to prevent crashes until configured
  const notConfiguredError = new Error('Supabase not configured. Open src/lib/supabase.ts and replace the SUPABASE PLACEHOLDER values with your Project URL and anon key from Project Settings → API.');
  supabase = {
    auth: {
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe() {} } } }),
      getSession: async () => ({ data: { session: null }, error: notConfiguredError }),
      signUp: async () => ({ data: null, error: notConfiguredError }),
      signInWithPassword: async () => ({ data: null, error: notConfiguredError }),
      signOut: async () => ({ error: notConfiguredError })
    }
  } as any;
}

export { supabase, supabaseUrl, supabaseAnonKey, isConfigured };
