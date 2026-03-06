import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { getConfig } from "../config";

let supabase: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (!supabase) {
    const config = getConfig();
    if (!config.telemetryEnabled || !config.supabaseUrl || !config.supabasePublishableKey) {
      throw new Error(
        "getSupabase() called with telemetry disabled. " +
          "This is a bug — recorder functions should guard before calling.",
      );
    }
    supabase = createClient(config.supabaseUrl, config.supabasePublishableKey);
  }
  return supabase;
}
