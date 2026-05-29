import { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "../lib/supabase";

const AuthContext = createContext(null);
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
const DEMO_TOKEN_KEY = "demoAccessToken";
const DEMO_USER_KEY = "demoUser";
const DEMO_EMAIL = import.meta.env.VITE_DEMO_LOGIN_EMAIL ?? "demo@student.test";
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_LOGIN_PASSWORD ?? "demo1234";

function readDemoUser() {
  const raw = localStorage.getItem(DEMO_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(DEMO_USER_KEY);
    localStorage.removeItem(DEMO_TOKEN_KEY);
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => readDemoUser());
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [onboardingRequired, setOnboardingRequired] = useState(false);

  async function getBackendAccountState(accessToken) {
    const response = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (response.status === 403) return { active: false, needsOnboarding: false };
    if (!response.ok) return { active: true, needsOnboarding: false };
    const data = await response.json().catch(() => null);
    return { active: true, needsOnboarding: data?.needs_onboarding === true };
  }

  async function completeOnboarding(onboarding) {
    const demoToken = localStorage.getItem(DEMO_TOKEN_KEY);
    const token = demoToken || session?.access_token;
    if (!token) throw new Error("Login is required.");
    const response = await fetch(`${API_BASE}/api/auth/complete-onboarding`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(onboarding),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(data?.detail || "Account setup failed.");
    }
    setOnboardingRequired(false);
    setUser((current) => current ? {
      ...current,
      user_metadata: {
        ...(current.user_metadata || {}),
        username: onboarding.username,
        nickname: current.user_metadata?.nickname || onboarding.username,
        accepted_terms: true,
        accepted_privacy: true,
      },
    } : current);
    return data;
  }

  async function applySupabaseSession(nextSession) {
    setSession(nextSession);
    if (!nextSession?.user) {
      setUser(null);
      setOnboardingRequired(false);
      setLoading(false);
      return;
    }
    const accountState = await getBackendAccountState(nextSession.access_token)
      .catch(() => ({ active: true, needsOnboarding: false }));
    if (!accountState.active) {
      await supabase.auth.signOut();
      setSession(null);
      setUser(null);
      setOnboardingRequired(false);
      setLoading(false);
      return;
    }
    setOnboardingRequired(accountState.needsOnboarding);
    setUser(nextSession.user);
    setLoading(false);
  }

  useEffect(() => {
    const demoUser = readDemoUser();
    if (demoUser) {
      setUser(demoUser);
      setLoading(false);
      return;
    }

    if (!supabase) { setLoading(false); return; }

    supabase.auth.getSession().then(({ data: { session } }) => {
      applySupabaseSession(session);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      applySupabaseSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  async function signInWithGoogle() {
    if (!supabase) throw new Error("Supabase not configured — add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to .env.local");
    localStorage.removeItem(DEMO_TOKEN_KEY);
    localStorage.removeItem(DEMO_USER_KEY);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin },
    });
    if (error) throw error;
  }

  async function signInWithPassword(email, password) {
    if (!supabase) throw new Error("Supabase not configured");
    localStorage.removeItem(DEMO_TOKEN_KEY);
    localStorage.removeItem(DEMO_USER_KEY);
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    return data;
  }

  async function signInWithDemo(email = DEMO_EMAIL, password = DEMO_PASSWORD) {
    const response = await fetch(`${API_BASE}/api/auth/demo-login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(data?.detail || "Demo login is not available.");
    }
    if (supabase) {
      await supabase.auth.signOut();
    }
    const demoUser = {
      id: data.user_id,
      email: data.email,
      user_metadata: {
        username: data.username,
        nickname: data.nickname,
        full_name: data.nickname,
      },
      app_metadata: { provider: "demo" },
    };
    localStorage.setItem(DEMO_TOKEN_KEY, data.access_token);
    localStorage.setItem(DEMO_USER_KEY, JSON.stringify(demoUser));
    setSession(null);
    setUser(demoUser);
    return { user: demoUser };
  }

  async function signUp(email, password, metadata = {}) {
    if (!supabase) throw new Error("Supabase not configured");
    localStorage.removeItem(DEMO_TOKEN_KEY);
    localStorage.removeItem(DEMO_USER_KEY);
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: metadata },
    });
    if (error) throw error;
    return data;
  }

  async function signOut() {
    localStorage.removeItem(DEMO_TOKEN_KEY);
    localStorage.removeItem(DEMO_USER_KEY);
    if (supabase) {
      await supabase.auth.signOut();
    }
    setSession(null);
    setUser(null);
    setOnboardingRequired(false);
  }

  async function deleteAccount() {
    const demoToken = localStorage.getItem(DEMO_TOKEN_KEY);
    const token = demoToken || session?.access_token;
    if (!token) throw new Error("Login is required.");
    const response = await fetch(`${API_BASE}/api/auth/delete-account`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(data?.detail || "Account deletion failed.");
    }
    await signOut();
    return data;
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, onboardingRequired, signInWithGoogle, signInWithPassword, signInWithDemo, signUp, signOut, deleteAccount, completeOnboarding, demoEmail: DEMO_EMAIL, demoPassword: DEMO_PASSWORD }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
