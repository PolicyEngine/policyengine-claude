import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { getConfig } from "../config";

let supabase: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (!supabase) {
    const config = getConfig();
    supabase = createClient(config.supabaseUrl, config.supabaseAnonKey);
  }
  return supabase;
}
