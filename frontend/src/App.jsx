import { useEffect, useRef, useState } from "react";
import { useAuth } from "./context/AuthContext";
import { supabase } from "./lib/supabase";
import LandingPage from "./components/LandingPage";
import PricingPage from "./components/PricingPage";

const WORD_LIMIT = 1200;
const FREE_WORD_LIMIT = 300;
const HUMANIZE_COST_PER_WORD = 5;
const HUMANIZE_MIN_CREDITS = 5000;

const ASSIGNMENT_TYPES = [
  { value: "general_academic", label: "Academic Paragraph" },
  { value: "discussion_post", label: "Discussion Post" },
  { value: "reflection_essay", label: "Reflection Essay" },
  { value: "research_essay", label: "Research Essay" },
  { value: "personal_statement", label: "Personal Statement" },
];

const WRITING_LEVELS = [
  { value: "esl_beginner", label: "ESL Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const DEPTH_OPTIONS = [
  { value: "basic", label: "Quick Check", costPerWord: 1, minCredits: 500, description: "Top 3 issues" },
  { value: "deep", label: "Deep Feedback", costPerWord: 2, minCredits: 1200, description: "Full analysis" },
  { value: "full_review", label: "Full Review", costPerWord: 5, minCredits: 3000, description: "Full analysis + examples" },
];

const TONE_OPTIONS = [
  { value: "natural_student", label: "Natural Student" },
  { value: "academic", label: "Academic" },
  { value: "simple_esl", label: "Simple ESL" },
];

const STRENGTH_OPTIONS = [
  { value: "light", label: "Light" },
  { value: "balanced", label: "Balanced" },
  { value: "strong", label: "Strong" },
];

const PERSONA_OPTIONS = [
  { value: "esl_student", label: "ESL Student" },
  { value: "freshman", label: "Freshman" },
  { value: "upper_division", label: "Upper-Division" },
  { value: "native_speaker", label: "Native Speaker" },
];

const ISSUE_LABELS = {
  ai_pattern: "AI Writing Pattern",
  unnatural_english: "Unnatural English",
  robotic_tone: "Robotic Tone",
  missing_example: "Missing Personal Voice",
  clarity_issue: "Clarity",
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

function countWords(text) {
  const tokens = text.trim().split(/\s+/).filter(Boolean);
  return tokens.reduce((sum, token) => {
    return sum + (token.length > 20 ? Math.ceil(token.length / 5) : 1);
  }, 0);
}

async function fetchJson(path, options = {}) {
  const session = supabase ? (await supabase.auth.getSession()).data.session : null;
  const demoToken = localStorage.getItem("demoAccessToken");
  const token = demoToken || session?.access_token;
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const raw = await response.text();
  let data = null;
  try {
    data = raw ? JSON.parse(raw) : null;
  } catch {
    throw new Error(`API returned a non-JSON response. Check that the backend is running on port 8000.`);
  }
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string"
      ? detail
      : detail?.message || data?.message || `Request failed for ${path}.`;
    const error = new Error(message);
    error.status = response.status;
    error.detail = detail;
    throw error;
  }
  return data;
}

function Collapsible({ label, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="collapsible">
      <button className="collapsible-header" onClick={() => setOpen(o => !o)}>
        <span>{label}</span>
        <span className={`collapsible-arrow${open ? " open" : ""}`}>›</span>
      </button>
      {open && <div className="collapsible-body">{children}</div>}
    </div>
  );
}

function ScoreCard({ label, score, invert = false }) {
  const raw = score >= 70 ? "high" : score >= 40 ? "medium" : "low";
  const colorClass = invert
    ? (raw === "high" ? "score-danger" : raw === "medium" ? "score-warn" : "score-good")
    : (raw === "high" ? "score-good" : raw === "medium" ? "score-warn" : "score-danger");
  return (
    <div className="score-card">
      <div className="score-label">{label}</div>
      <div className={`score-value ${colorClass}`}>{score}</div>
      <div className={`score-level ${colorClass}`}>{raw.toUpperCase()}</div>
    </div>
  );
}

export default function App() {
  const { user, loading: authStateLoading, onboardingRequired, signInWithGoogle, signInWithPassword, signInWithDemo, signUp: supabaseSignUp, signOut: supabaseSignOut, deleteAccount, completeOnboarding, demoEmail, demoPassword } = useAuth();
  const [showEditor, setShowEditor] = useState(() => localStorage.getItem("showEditor") === "true");

  useEffect(() => {
    localStorage.setItem("showEditor", showEditor);
  }, [showEditor]);
  const [text, setText] = useState("");
  const [assignmentType, setAssignmentType] = useState("general_academic");
  const [writingLevel, setWritingLevel] = useState("intermediate");
  const [depth, setDepth] = useState("deep");
  const [result, setResult] = useState(null);
  const [feedbackOpen, setFeedbackOpen] = useState(true);
  const [humanizeOpen, setHumanizeOpen] = useState(true);
  const [billing, setBilling] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [humanizeResult, setHumanizeResult] = useState(null);
  const [humanizeLoading, setHumanizeLoading] = useState(false);
  const [showHumanizeModal, setShowHumanizeModal] = useState(false);
  const [humanizeTone, setHumanizeTone] = useState("natural_student");
  const [humanizeStrength, setHumanizeStrength] = useState("balanced");
  const [humanizePersona, setHumanizePersona] = useState("esl_student");
  const [coachFeedback, setCoachFeedback] = useState(null);
  const [preserveMeaning, setPreserveMeaning] = useState(true);
  const [preserveCitations, setPreserveCitations] = useState(false);
  const [preserveStructure, setPreserveStructure] = useState(false);

  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("darkMode") === "true");
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState("login"); // "login" | "register" | "google" | "verify"
  const [authEmail, setAuthEmail] = useState("");
  const [authUsername, setAuthUsername] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authPasswordConfirm, setAuthPasswordConfirm] = useState("");
  const [emailAvail, setEmailAvail] = useState(null);
  const [usernameAvail, setUsernameAvail] = useState(null);
  const [emailChecking, setEmailChecking] = useState(false);
  const [usernameChecking, setUsernameChecking] = useState(false);
  const [tosAgreed, setTosAgreed] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showPricing, setShowPricing] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(null);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [showLimitCta, setShowLimitCta] = useState(false);
  const [limitNotice, setLimitNotice] = useState(null);
  const [accountDeleting, setAccountDeleting] = useState(false);

  useEffect(() => {
    localStorage.setItem("darkMode", darkMode);
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("payment_success") === "1") {
      window.history.replaceState({}, "", window.location.pathname);
      setPaymentSuccess(true);
      if (user) {
        fetchJson("/api/billing/status").then(setBilling).catch(() => null);
      }
    }
  }, [user]);

  const resultRef = useRef(null);
  const humanizeResultRef = useRef(null);
  const profileMenuRef = useRef(null);

  useEffect(() => {
    if (!profileOpen) return;
    function handleClickOutside(e) {
      if (profileMenuRef.current && !profileMenuRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [profileOpen]);

  useEffect(() => {
    if (!result) return;
    const timer = setTimeout(() => {
      if (!resultRef.current) return;
      const y = resultRef.current.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: y, behavior: "smooth" });
    }, 80);
    return () => clearTimeout(timer);
  }, [result]);

  useEffect(() => {
    if (!humanizeResult || humanizeLoading) return;
    const timer = setTimeout(() => {
      if (!humanizeResultRef.current) return;
      const y = humanizeResultRef.current.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: y, behavior: "smooth" });
    }, 80);
    return () => clearTimeout(timer);
  }, [humanizeResult, humanizeLoading]);

  const wordCount = countWords(text);
  const overLimit = wordCount > WORD_LIMIT;
  const isFreePlan = billing?.subscription_status === "free";
  const freeLimitWarning = isFreePlan && wordCount > FREE_WORD_LIMIT;
  const usageLimit = billing?.usage_limit ?? billing?.monthly_credit_limit ?? 0;
  const usageUsed = billing?.usage_used ?? Math.max(0, usageLimit - (billing?.credits_remaining ?? 0));
  const usagePercent = usageLimit > 0
    ? Math.min(100, billing?.usage_percent ?? Math.round((usageUsed / usageLimit) * 100))
    : 0;
  const usageWarning = !isFreePlan && usageLimit > 0 && usagePercent >= 80 && usagePercent < 100;
  const usageExhausted = !isFreePlan && usageLimit > 0 && usagePercent >= 100;

  const selectedDepth = DEPTH_OPTIONS.find((d) => d.value === depth);
  const feedbackCost = isFreePlan ? 0 : Math.max(
    wordCount * (selectedDepth?.costPerWord ?? 2),
    selectedDepth?.minCredits ?? 1200,
  );
  const humanizeCost = isFreePlan ? 0 : Math.max(wordCount * HUMANIZE_COST_PER_WORD, HUMANIZE_MIN_CREDITS);
  const canSubmit = text.trim() && !overLimit && !loading && !humanizeLoading;

  useEffect(() => {
    if (!user) {
      setBilling(null);
      return;
    }
    fetchJson("/api/billing/status")
      .then(setBilling)
      .catch(() => setBilling(null));
  }, [user]);

  useEffect(() => {
    if (!usageExhausted) return;
    setLimitNotice({
      message: "You've used this month's included credits.",
      recommended_offer: "Upgrade your plan or add a credit pack to keep working.",
    });
    setShowLimitCta(true);
  }, [usageExhausted]);

  // Protect editor: redirect to landing + open auth modal when not logged in
  useEffect(() => {
    if (showEditor && !authStateLoading && !user) {
      setShowEditor(false);
      setShowAuthModal(true);
    }
  }, [showEditor, user, authStateLoading]);

  useEffect(() => {
    if (!onboardingRequired) return;
    setAuthMode("google");
    setAuthUsername("");
    setUsernameAvail(null);
    setTosAgreed(false);
    setAuthError("");
    setShowAuthModal(true);
  }, [onboardingRequired]);

  async function handleCoach() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await fetchJson("/api/coach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, assignment_type: assignmentType, writing_level: writingLevel, depth }),
      });
      setResult(data);
      setFeedbackOpen(true);
      setCoachFeedback(data.feedback_items?.length ? data.feedback_items : null);
      if (data.billing_redirect) setError(data.billing_redirect.message);
      setBilling(await fetchJson("/api/billing/status"));
    } catch (err) {
      if (err.status === 429 && err.detail) {
        setLimitNotice(err.detail);
        setShowLimitCta(true);
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleHumanize() {
    setShowHumanizeModal(false);
    setHumanizeLoading(true);
    setHumanizeResult(null);
    try {
      const data = await fetchJson("/api/humanize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          tone: humanizeTone,
          strength: humanizeStrength,
          persona: humanizePersona,
          coach_feedback: coachFeedback,
          preserve_meaning: preserveMeaning,
          preserve_citations: preserveCitations,
          preserve_structure: preserveStructure,
        }),
      });
      setHumanizeResult(data);
      setHumanizeOpen(true);
      if (data.billing_redirect) setError(data.billing_redirect.message);
      setBilling(await fetchJson("/api/billing/status"));
    } catch (err) {
      if (err.status === 429 && err.detail) {
        setLimitNotice(err.detail);
        setShowLimitCta(true);
      }
      setError(err.message);
    } finally {
      setHumanizeLoading(false);
    }
  }

  async function startCheckout(productCode) {
    if (!user) {
      setError("결제를 진행하려면 먼저 로그인해주세요.");
      openAuth("login");
      return false;
    }
    setCheckoutLoading(productCode);
    try {
      const data = await fetchJson("/api/billing/checkout", {
        method: "POST",
        body: JSON.stringify({
          product_code: productCode,
          success_url: `${window.location.origin}/?payment_success=1`,
        }),
      });
      if (!data?.checkout_url) {
        throw new Error("결제 페이지 URL을 받지 못했습니다.");
      }
      window.location.href = data.checkout_url;
      return true;
    } catch (err) {
      console.error("[Checkout] API error:", err);
      setError(err.message ?? "결제 페이지 이동에 실패했습니다.");
      return false;
    } finally {
      setCheckoutLoading(null);
    }
  }


  async function handleLogout() {
    await supabaseSignOut();
    setProfileOpen(false);
    setBilling(null);
    setShowEditor(false);
  }

  async function handleDeleteAccount() {
    if (!window.confirm("Delete this account? You will be signed out and cannot use the app with this account again.")) {
      return;
    }
    setAccountDeleting(true);
    setError("");
    try {
      await deleteAccount();
      setProfileOpen(false);
      setBilling(null);
      setShowEditor(false);
      setResult(null);
      setHumanizeResult(null);
    } catch (err) {
      setError(err.message ?? "Account deletion failed.");
    } finally {
      setAccountDeleting(false);
    }
  }

  function openAuth(mode = "login") {
    setAuthMode(mode);
    setAuthEmail(""); setEmailAvail(null);
    setAuthUsername(""); setUsernameAvail(null);
    setAuthPassword("");
    setAuthPasswordConfirm("");
    setTosAgreed(false);
    setAuthError("");
    setShowAuthModal(true);
    setProfileOpen(false);
  }

  async function checkUsername() {
    if (!authUsername) return;
    setUsernameChecking(true);
    try {
      const data = await fetchJson(`/api/auth/check-username?username=${encodeURIComponent(authUsername)}`);
      setUsernameAvail(data.available);
    } catch { setUsernameAvail(false); }
    finally { setUsernameChecking(false); }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError("");
    try {
      const { session: newSession } = await supabaseSignUp(authEmail, authPassword, {
        username: authUsername,
        nickname: authUsername,
        accepted_terms: true,
        accepted_privacy: true,
      });
      if (newSession) {
        setShowAuthModal(false);
      } else {
        setAuthMode("verify");
      }
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError("");
    try {
      await signInWithPassword(authEmail, authPassword);
      setShowAuthModal(false);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleGoogleStart() {
    setAuthLoading(true);
    setAuthError("");
    try {
      await signInWithGoogle();
    } catch (err) {
      setAuthError(err.message);
      setAuthLoading(false);
    }
  }

  async function handleGoogleOnboarding(e) {
    e.preventDefault();
    const username = authUsername.trim();
    if (!/^[a-zA-Z0-9_]{3,50}$/.test(username)) {
      setAuthError("Username must use 3-50 letters, numbers, or underscores.");
      return;
    }
    if (!tosAgreed) {
      setAuthError("Please agree to the Terms of Service and Privacy Policy.");
      return;
    }
    setAuthLoading(true);
    setAuthError("");
    try {
      await completeOnboarding({
        username,
        accepted_terms: true,
        accepted_privacy: true,
      });
      setShowAuthModal(false);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleDemoSignIn() {
    setAuthLoading(true);
    setAuthError("");
    try {
      await signInWithDemo();
      setShowAuthModal(false);
      setShowEditor(true);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  const planInitial = user
    ? (user.user_metadata?.full_name || user.email)[0].toUpperCase()
    : (billing?.plan_name ?? "F")[0].toUpperCase();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <button
            className="brand-lockup brand-home-btn"
            onClick={() => setShowEditor(false)}
            aria-label="Home"
          >
            <div className="brand-logo" aria-hidden="true">
              <svg className="brand-logo-icon" viewBox="0 0 64 64" role="img">
                <path className="brand-spark brand-spark-large" d="M11 5.5l2.1 6.1 6.1 2.1-6.1 2.1L11 21.9l-2.1-6.1-6.1-2.1 6.1-2.1L11 5.5z" />
                <path className="brand-spark brand-spark-small" d="M4.7 20.4l1.4 4.2 4.2 1.4-4.2 1.4-1.4 4.2-1.4-4.2L-.9 26l4.2-1.4 1.4-4.2z" />
                <path className="brand-page" d="M17 10h26l9 9v28a7 7 0 0 1-7 7H21l-9 8V17a7 7 0 0 1 7-7z" />
                <path className="brand-page-fold" d="M43 10v10h9" />
                <path className="brand-line" d="M23 25h16" />
                <path className="brand-line" d="M23 34h16" />
                <path className="brand-line short" d="M23 43h11" />
                <path className="brand-pen" d="M36 39l23-7-7 23-18 5 5-18z" />
                <path className="brand-pen-stroke" d="M35 59l16-16" />
                <circle className="brand-pen-dot" cx="50" cy="42" r="3" />
              </svg>
              <span className="brand-wordmark">
                <span>EssayCoach</span>
                <span>AI</span>
              </span>
            </div>
          </button>
          <nav className="topnav">
            {billing && !isFreePlan && (
              <div className={`nav-credits ${
                billing.credits_remaining < 1000 ? "nav-credits-critical" :
                billing.credits_remaining < 5000 ? "nav-credits-low" : ""
              }`}>
                <span className="nav-plan-name">{billing.plan_name}</span>
                <span className="nav-credit-count">{billing.credits_remaining.toLocaleString()} cr</span>
              </div>
            )}
            <button className="topnav-cta" onClick={() => setShowPricing(true)}>
              Upgrade
            </button>
            <div className="profile-menu-wrap" ref={profileMenuRef}>
              <button
                className="profile-avatar-btn"
                onClick={() => setProfileOpen(o => !o)}
                aria-label="Profile"
              >
                <span>{planInitial}</span>
              </button>

              {profileOpen && (
                <div className="profile-dropdown">
                {user ? (
                  <div className="pd-account-row">
                    <div>
                      <div className="pd-user-nickname">{user.user_metadata?.full_name || user.user_metadata?.nickname || user.email}</div>
                      <div className="pd-user-handle">{user.user_metadata?.username ? `@${user.user_metadata.username}` : user.email}</div>
                    </div>
                    {billing && <div className="pd-plan-badge">{billing.plan_name}</div>}
                  </div>
                ) : billing && (
                  <div className="pd-account-row">
                    <div className="pd-plan-badge">{billing.plan_name} Plan</div>
                    <div className="pd-credits-val">{billing.credits_remaining?.toLocaleString()} cr</div>
                  </div>
                )}
                <div className="pd-divider" />
                {user ? (
                  <button className="pd-item" onClick={handleLogout}>
                    <span className="pd-icon">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                    </span>
                    Log out
                  </button>
                ) : (
                  <button className="pd-item" onClick={() => openAuth("login")}>
                    <span className="pd-icon">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
                    </span>
                    Log in / Sign up
                  </button>
                )}
                {user && user.app_metadata?.provider !== "demo" && (
                  <button className="pd-item pd-item-danger" onClick={handleDeleteAccount} disabled={accountDeleting}>
                    <span className="pd-icon">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                    </span>
                    {accountDeleting ? "Deleting..." : "Delete account"}
                  </button>
                )}
                <div className="pd-item pd-item-toggle" onClick={() => setDarkMode(d => !d)}>
                  <span className="pd-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
                  </span>
                  <span className="pd-item-label">Dark mode</span>
                  <div className={`pd-toggle ${darkMode ? "on" : ""}`}>
                    <div className="pd-toggle-knob" />
                  </div>
                </div>
                <a className="pd-item" href="/help.html" target="_blank" rel="noopener" onClick={() => setProfileOpen(false)}>
                  <span className="pd-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  </span>
                  Help Center
                </a>
                <a className="pd-item" href="mailto:contact@writingcoach.ai" onClick={() => setProfileOpen(false)}>
                  <span className="pd-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                  </span>
                  Contact us
                </a>
                <div className="pd-divider" />
                <a className="pd-item pd-item-arrow" href="/terms.html" target="_blank" rel="noopener" onClick={() => setProfileOpen(false)}>
                  <span className="pd-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  </span>
                  Terms of Service
                  <svg className="pd-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
                </a>
                <a className="pd-item pd-item-arrow" href="/privacy.html" target="_blank" rel="noopener" onClick={() => setProfileOpen(false)}>
                  <span className="pd-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                  </span>
                  Privacy Policy
                  <svg className="pd-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
                </a>
                </div>
              )}
            </div>
          </nav>
        </div>
      </header>

      {/* ── Payment success banner ── */}
      {paymentSuccess && (
        <div className="payment-success-banner" onClick={() => setPaymentSuccess(false)}>
          결제가 완료되었습니다! 플랜이 업그레이드되었어요. ✓
          <span className="payment-success-dismiss">✕</span>
        </div>
      )}

      {/* ── Pricing page ── */}
      {showPricing && (
        <PricingPage
          onClose={() => setShowPricing(false)}
          onCheckout={async (code) => { const ok = await startCheckout(code); if (ok) setShowPricing(false); }}
          currentStatus={billing?.subscription_status}
          loading={checkoutLoading}
        />
      )}

      {showLimitCta && (
        <div className="usage-limit-overlay" onClick={() => setShowLimitCta(false)}>
          <div className="usage-limit-modal" onClick={(e) => e.stopPropagation()}>
            <button className="auth-modal-close" onClick={() => setShowLimitCta(false)}>✕</button>
            <div className="eyebrow">Usage limit</div>
            <h3>{limitNotice?.message || "You reached your usage limit."}</h3>
            <p>{limitNotice?.recommended_offer || "Upgrade your plan or add credits to continue."}</p>
            <button className="topnav-cta" onClick={() => { setShowLimitCta(false); setShowPricing(true); }}>
              Upgrade
            </button>
          </div>
        </div>
      )}

      {/* ── Humanize modal ── */}
      {showHumanizeModal && (
        <div className="humanize-modal-overlay" onClick={() => setShowHumanizeModal(false)}>
          <div className="humanize-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Humanize Options</h3>
            <div className="option-group">
              <div className="option-label">Tone</div>
              <div className="toggle-row">
                {TONE_OPTIONS.map((t) => (
                  <button key={t.value}
                    className={`toggle-btn ${humanizeTone === t.value ? "active" : ""}`}
                    onClick={() => setHumanizeTone(t.value)}>{t.label}</button>
                ))}
              </div>
            </div>
            <div className="option-group">
              <div className="option-label">Strength</div>
              <div className="toggle-row">
                {STRENGTH_OPTIONS.map((s) => (
                  <button key={s.value}
                    className={`toggle-btn ${humanizeStrength === s.value ? "active" : ""}`}
                    onClick={() => setHumanizeStrength(s.value)}>{s.label}</button>
                ))}
              </div>
            </div>
            {coachFeedback && (
              <div className="coach-hint">
                Coach analysis will guide this rewrite ({coachFeedback.length} issues found)
              </div>
            )}
            <div className="option-group">
              <div className="option-label">Preserve</div>
              <div className="preserve-row">
                <label><input type="checkbox" checked={preserveMeaning} onChange={(e) => setPreserveMeaning(e.target.checked)} /> Original meaning</label>
                <label><input type="checkbox" checked={preserveCitations} onChange={(e) => setPreserveCitations(e.target.checked)} /> Citations</label>
                <label><input type="checkbox" checked={preserveStructure} onChange={(e) => setPreserveStructure(e.target.checked)} /> Structure</label>
              </div>
            </div>
            <div className="option-group">
              <div className="option-label">Writing Persona</div>
              <div className="toggle-row">
                {PERSONA_OPTIONS.map((p) => (
                  <button key={p.value}
                    className={`toggle-btn ${humanizePersona === p.value ? "active" : ""}`}
                    onClick={() => setHumanizePersona(p.value)}>{p.label}</button>
                ))}
              </div>
            </div>
            <div className="modal-actions">
              <button className="secondary" onClick={() => setShowHumanizeModal(false)}>Cancel</button>
              <button onClick={handleHumanize}>Run Humanize →</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Auth modal ── */}
      {showAuthModal && (
        <div className="auth-modal-overlay" onClick={() => setShowAuthModal(false)}>
          <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
            <button className="auth-modal-close" onClick={() => setShowAuthModal(false)}>✕</button>

            {authMode === "verify" && (
              <div className="auth-modal-header">
                <h3>Check your email</h3>
                <p>We sent a confirmation link to <strong>{authEmail}</strong>. Click the link to activate your account.</p>
              </div>
            )}

            {authMode === "register" && (
              <>
                <div className="auth-modal-header">
                  <h3>Create account</h3>
                  <p>Start coaching your ESL academic writing for free.</p>
                </div>
                <button type="button" className="auth-google-btn" onClick={handleGoogleStart} disabled={authLoading}>
                  <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853"/><path d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>
                  Continue with Google
                </button>
                <button type="button" className="auth-demo-btn" onClick={handleDemoSignIn} disabled={authLoading}>
                  {authLoading ? "Opening demo..." : "Use demo account"}
                </button>
                <div className="auth-demo-hint">
                  Test ID: {demoEmail} · Password: {demoPassword}
                </div>
                <div className="auth-divider"><span>or</span></div>
                <form onSubmit={handleRegister}>
                  <div className="auth-field">
                    <label>Email</label>
                    <input type="email" value={authEmail} onChange={(e) => setAuthEmail(e.target.value)} placeholder="you@email.com" required autoFocus />
                  </div>
                  <div className="auth-field">
                    <label>Username</label>
                    <div className="auth-check-row">
                      <input type="text" value={authUsername} onChange={(e) => { setAuthUsername(e.target.value); setUsernameAvail(null); }} placeholder="letters, numbers, _ (3+ chars)" required minLength={3} maxLength={50} pattern="^[a-zA-Z0-9_]+$" title="Letters, numbers, and underscores only" />
                      <button type="button" className="auth-check-btn" onClick={checkUsername} disabled={!authUsername || usernameChecking}>
                        {usernameChecking ? "…" : "Check"}
                      </button>
                    </div>
                    {usernameAvail === true && <div className="auth-avail-ok">✓ Username is available</div>}
                    {usernameAvail === false && <div className="auth-avail-fail">✗ Username is already taken</div>}
                  </div>
                  <div className="auth-field">
                    <label>Password</label>
                    <input type="password" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} placeholder="8+ characters" required />
                  </div>
                  <div className="auth-field">
                    <label>Confirm password</label>
                    <input type="password" value={authPasswordConfirm} onChange={(e) => setAuthPasswordConfirm(e.target.value)} placeholder="Re-enter your password" required />
                  </div>
                  <label className="auth-tos-label">
                    <input type="checkbox" checked={tosAgreed} onChange={(e) => setTosAgreed(e.target.checked)} />
                    <span>I agree to the <a href="/terms.html" target="_blank" rel="noopener">Terms of Service</a> and <a href="/privacy.html" target="_blank" rel="noopener">Privacy Policy</a></span>
                  </label>
                  {authError && <div className="auth-error">{authError}</div>}
                  <button type="submit" className="auth-submit-btn" disabled={authLoading || usernameAvail !== true || !tosAgreed}>
                    {authLoading ? "Creating account…" : "Create account →"}
                  </button>
                  {usernameAvail !== true && !authLoading && (
                    <div className="auth-check-hint">Please check username availability</div>
                  )}
                </form>
                <div className="auth-switch">
                  Already have an account?{" "}
                  <button type="button" className="auth-link" onClick={() => openAuth("login")}>Log in</button>
                </div>
              </>
            )}

            {authMode === "google" && (
              <>
                <div className="auth-modal-header">
                  <h3>Finish Google sign up</h3>
                  <p>Add a username so your account is easy to find later.</p>
                </div>
                <form onSubmit={handleGoogleOnboarding}>
                  <div className="auth-field">
                    <label>Username</label>
                    <input type="text" value={authUsername} onChange={(e) => setAuthUsername(e.target.value)} placeholder="letters, numbers, _ (3+ chars)" required minLength={3} maxLength={50} pattern="^[a-zA-Z0-9_]+$" title="Letters, numbers, and underscores only" autoFocus />
                  </div>
                  <label className="auth-tos-label">
                    <input type="checkbox" checked={tosAgreed} onChange={(e) => setTosAgreed(e.target.checked)} />
                    <span>I agree to the <a href="/terms.html" target="_blank" rel="noopener">Terms of Service</a> and <a href="/privacy.html" target="_blank" rel="noopener">Privacy Policy</a></span>
                  </label>
                  {authError && <div className="auth-error">{authError}</div>}
                  <button type="submit" className="auth-google-btn" disabled={authLoading || !authUsername.trim() || !tosAgreed}>
                    <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853"/><path d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>
                    {authLoading ? "Opening Google..." : "Continue with Google"}
                  </button>
                </form>
                <div className="auth-switch">
                  Use email instead?{" "}
                  <button type="button" className="auth-link" onClick={() => openAuth("register")}>Create account</button>
                </div>
              </>
            )}

            {authMode === "login" && (
              <>
                <div className="auth-modal-header">
                  <h3>Welcome back</h3>
                  <p>Log in to your Writing Coach account.</p>
                </div>
                <button type="button" className="auth-google-btn" onClick={handleGoogleStart} disabled={authLoading}>
                  <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853"/><path d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>
                  Continue with Google
                </button>
                <button type="button" className="auth-demo-btn" onClick={handleDemoSignIn} disabled={authLoading}>
                  {authLoading ? "Opening demo..." : "Use demo account"}
                </button>
                <div className="auth-demo-hint">
                  Test ID: {demoEmail} · Password: {demoPassword}
                </div>
                <div className="auth-divider"><span>or</span></div>
                <form onSubmit={handleLogin}>
                  <div className="auth-field">
                    <label>Email</label>
                    <input type="email" value={authEmail} onChange={(e) => setAuthEmail(e.target.value)} placeholder="you@email.com" required autoFocus />
                  </div>
                  <div className="auth-field">
                    <label>Password</label>
                    <input type="password" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} placeholder="Password" required />
                  </div>
                  {authError && <div className="auth-error">{authError}</div>}
                  <button type="submit" className="auth-submit-btn" disabled={authLoading}>
                    {authLoading ? "Signing in..." : "Log In →"}
                  </button>
                </form>
                <div className="auth-switch">
                  No account?{" "}
                  <button type="button" className="auth-link" onClick={() => openAuth("register")}>Sign up free</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Upgrade modal ── */}
      {showUpgradeModal && (
        <div className="auth-modal-overlay" onClick={() => setShowUpgradeModal(false)}>
          <div className="upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <div className="upgrade-modal-head">
              <div>
                <div className="eyebrow">Pricing</div>
                <h3>Choose Your Plan</h3>
              </div>
              <button className="auth-modal-close upgrade-modal-close" onClick={() => setShowUpgradeModal(false)}>✕</button>
            </div>

            <div className="upgrade-plans-grid">
              {[
                { code: null, name: "Free", price: 0, unit: "", credits: "300 words/day", desc: "1 analysis/day, no credit card" },
                { code: "starter_monthly", name: "Starter", price: 7, unit: "/mo", credits: "20K credits/mo", desc: "~10 deep analyses" },
                { code: "student_plus_monthly", name: "Student Plus", price: 12, unit: "/mo", credits: "60K credits/mo", desc: "Most popular ★", featured: true },
                { code: "pro_monthly", name: "Pro", price: 19, unit: "/mo", credits: "150K credits/mo", desc: "Power users" },
              ].map((plan) => (
                <div key={plan.name} className={`upgrade-plan-card${plan.featured ? " upgrade-plan-featured" : ""}`}>
                  {plan.featured && <div className="upgrade-plan-badge">Most Popular</div>}
                  <div className="upgrade-plan-name">{plan.name}</div>
                  <div className="upgrade-plan-price">${plan.price}<span>{plan.unit}</span></div>
                  <div className="upgrade-plan-credits">{plan.credits}</div>
                  <div className="upgrade-plan-desc">{plan.desc}</div>
                  {plan.code ? (
                    <button className={`upgrade-plan-btn${plan.featured ? " upgrade-plan-btn-primary" : ""}`} onClick={() => { startCheckout(plan.code); setShowUpgradeModal(false); }}>
                      {plan.featured ? "Start Free Trial →" : "Choose Plan"}
                    </button>
                  ) : (
                    <button className="upgrade-plan-btn upgrade-plan-btn-muted" disabled>Free</button>
                  )}
                </div>
              ))}
            </div>

            <div className="upgrade-packs-section">
              <div className="upgrade-packs-title">Credit Packs — One-time purchase</div>
              <div className="upgrade-packs-row">
                {[
                  { code: "credit_pack_s", label: "$5", sub: "25K credits" },
                  { code: "credit_pack_m", label: "$10", sub: "60K credits" },
                  { code: "credit_pack_l", label: "$20", sub: "150K credits" },
                ].map((pack) => (
                  <button key={pack.code} className="upgrade-pack-btn" onClick={() => { startCheckout(pack.code); setShowUpgradeModal(false); }}>
                    <span className="upgrade-pack-price">{pack.label}</span>
                    <span className="upgrade-pack-sub">{pack.sub}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Hero landing page ── */}
      {!showEditor && (
        <LandingPage
          onStart={() => setShowEditor(true)}
          onUpgrade={() => setShowPricing(true)}
        />
      )}

      {/* ── Editor page ── */}
      {showEditor && (
        <main className="workspace">

          <section className="editor-card">
            {billing && !isFreePlan && (
              <div className={`usage-panel${usageWarning ? " usage-panel-warning" : ""}${usageExhausted ? " usage-panel-exhausted" : ""}`}>
                <div className="usage-panel-head">
                  <div>
                    <div className="eyebrow">Monthly usage</div>
                    <strong>{usageUsed.toLocaleString()} / {usageLimit.toLocaleString()} credits</strong>
                  </div>
                  <span>{usagePercent}%</span>
                </div>
                <div className="usage-progress">
                  <div style={{ width: `${usagePercent}%` }} />
                </div>
                {usageWarning && (
                  <div className="usage-warning">You're near this month's included credit limit.</div>
                )}
              </div>
            )}
            <div className="editor-toolbar">
              <div>
                <div className="eyebrow">Workspace</div>
                <h2>Paste your essay below.</h2>
              </div>
            </div>

            <div className="editor-grid">
              <div className="input-panel">
                <label htmlFor="essay-input">Your essay or paragraph</label>
                <textarea
                  id="essay-input"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste your essay here..."
                  rows={25}
                />
                <div className={`word-counter ${overLimit ? "danger" : ""}`}>
                  {wordCount} / {WORD_LIMIT} words
                  {isFreePlan && !overLimit && (
                    <span className="free-limit-note"> · Free plan: {FREE_WORD_LIMIT} word max</span>
                  )}
                </div>
                {overLimit && <div className="inline-error">Over the 1,200-word limit.</div>}
                {freeLimitWarning && !overLimit && (
                  <div className="inline-error">
                    Free plan is limited to {FREE_WORD_LIMIT} words. Upgrade to analyze longer essays.
                  </div>
                )}
              </div>

              <div className="requirements-card">
                <div className="requirements-header">
                  <h3>Options</h3>
                  <p>Choose your assignment type, level, and feedback depth.</p>
                </div>

                <div className="coach-selects">
                  <div className="select-group">
                    <label className="select-label">Assignment Type</label>
                    <select className="coach-select" value={assignmentType}
                      onChange={(e) => setAssignmentType(e.target.value)}>
                      {ASSIGNMENT_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="select-group">
                    <label className="select-label">Writing Level</label>
                    <select className="coach-select" value={writingLevel}
                      onChange={(e) => setWritingLevel(e.target.value)}>
                      {WRITING_LEVELS.map((l) => (
                        <option key={l.value} value={l.value}>{l.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="depth-row">
                  {DEPTH_OPTIONS.map((opt) => (
                    <button key={opt.value} type="button"
                      className={`depth-btn ${depth === opt.value ? "active" : ""}`}
                      onClick={() => setDepth(opt.value)}>
                      <span className="depth-name">{opt.label}</span>
                      <span className="depth-desc">{opt.description}</span>
                      <span className="depth-cost">
                        {isFreePlan
                          ? (opt.value === "basic" ? "Free" : "Paid")
                          : `~${Math.max(wordCount * opt.costPerWord, opt.minCredits).toLocaleString()} cr`}
                      </span>
                    </button>
                  ))}
                </div>

                <div className="dual-action-row">
                  <button className="btn-feedback" disabled={!canSubmit} onClick={handleCoach}>
                    <span className="btn-action-title">
                      {loading ? "Analyzing..." : "Get Feedback"}
                    </span>
                    <span className="btn-action-cost">
                      {isFreePlan ? "Free · 300 words" : `~${feedbackCost.toLocaleString()} cr`}
                    </span>
                  </button>
                  <button className="btn-humanize-action" disabled={!canSubmit} onClick={() => setShowHumanizeModal(true)}>
                    <span className="btn-action-title">
                      {humanizeLoading ? "Humanizing..." : "Humanize Essay"}
                    </span>
                    <span className="btn-action-cost">
                      {isFreePlan ? "Upgrade required" : `~${humanizeCost.toLocaleString()} cr`}
                    </span>
                  </button>
                </div>
              </div>
            </div>

            {error && <div className="inline-error inline-banner">{error}</div>}
          </section>

          {/* Feedback result */}
          {result && !result.billing_redirect && (
            <section className="result-card" id="results" ref={resultRef}>
              <button className="card-toggle-header" onClick={() => setFeedbackOpen(o => !o)}>
                <div className="result-header-inner">
                  <div>
                    <div className="eyebrow">Writing Analysis</div>
                    <h2>Your Writing Scores</h2>
                  </div>
                  <div className="card-toggle-right">
                    <div className={`verdict ${result.verdict_label}`}>
                      {result.verdict_label === "high" ? "High AI-like"
                        : result.verdict_label === "medium" ? "Some AI patterns"
                        : "Mostly Human"}
                    </div>
                    <span className={`collapsible-arrow${feedbackOpen ? " open" : ""}`}>›</span>
                  </div>
                </div>
              </button>

              {feedbackOpen && (
                <>
                  <div className="score-grid">
                    <ScoreCard label="AI-Like Writing" score={result.ai_like_score} invert />
                    <ScoreCard label="Naturalness" score={result.naturalness_score} />
                    <ScoreCard label="Personal Voice" score={result.personal_voice_score} />
                    <ScoreCard label="Clarity" score={result.clarity_score} />
                  </div>

                  <p className="result-summary-text">{result.overall_summary}</p>

                  {result.signals?.length > 0 && (
                    <Collapsible label="Detected Patterns">
                      <div className="signal-list">
                        {result.signals.map((s, i) => <span key={i}>{s}</span>)}
                      </div>
                    </Collapsible>
                  )}

                  {result.strengths.length > 0 && (
                    <Collapsible label="What's working well">
                      <div className="signal-list">
                        {result.strengths.map((s, i) => <span key={i} className="strength-chip">{s}</span>)}
                      </div>
                    </Collapsible>
                  )}

                  {result.feedback_items.length > 0 && (
                    <Collapsible label="Writing Issues">
                      {result.feedback_items.map((item, i) => (
                        <div key={i} className={`feedback-item issue-${item.issue_type}`}>
                          <div className="feedback-header">
                            <span className="issue-badge">{ISSUE_LABELS[item.issue_type] ?? item.issue_type}</span>
                            <span className={`severity-badge severity-${item.severity}`}>
                              {item.severity?.toUpperCase()}
                            </span>
                          </div>
                          <blockquote className="feedback-quote">"{item.sentence}"</blockquote>
                          <p className="feedback-explanation">{item.explanation}</p>
                          <div className="feedback-suggestion">
                            <span className="suggestion-label">Try this:</span> {item.suggestion}
                          </div>
                        </div>
                      ))}
                    </Collapsible>
                  )}

                  <div className="credits-footer">
                    Credits used: <strong>{result.credits_charged}</strong>
                    {" · "}
                    Remaining: <strong>{result.credits_remaining.toLocaleString()}</strong>
                  </div>
                </>
              )}
            </section>
          )}

          {humanizeLoading && (
            <section className="result-card">
              <div className="humanize-loading">Humanizing your essay...</div>
            </section>
          )}

          {humanizeResult && !humanizeResult.billing_redirect && (
            <section className="result-card" ref={humanizeResultRef}>
              <button className="card-toggle-header" onClick={() => setHumanizeOpen(o => !o)}>
                <div className="result-header-inner">
                  <div>
                    <div className="eyebrow">Humanized</div>
                    <h2>{humanizeResult.summary_of_changes}</h2>
                  </div>
                  <div className="card-toggle-right">
                    <div className="verdict humanized">Rewritten</div>
                    <span className={`collapsible-arrow${humanizeOpen ? " open" : ""}`}>›</span>
                  </div>
                </div>
              </button>
              {humanizeOpen && (
                <>
                  <div className="compare-grid">
                    <div>
                      <div className="compare-label">Original</div>
                      <div className="compare-text">{text}</div>
                    </div>
                    <div>
                      <div className="compare-label">Humanized</div>
                      <div className="compare-text">{humanizeResult.rewritten_text}</div>
                    </div>
                  </div>
                  {humanizeResult.key_improvements?.length > 0 && (
                    <Collapsible label="Key improvements">
                      <ul className="improvements-list">
                        {humanizeResult.key_improvements.map((imp, i) => <li key={i}>{imp}</li>)}
                      </ul>
                    </Collapsible>
                  )}
                  <div className="credits-footer">
                    Credits used: <strong>{humanizeResult.credits_charged}</strong>
                    {" · "}
                    Remaining: <strong>{humanizeResult.credits_remaining.toLocaleString()}</strong>
                  </div>
                </>
              )}
            </section>
          )}

          {result?.billing_redirect && (
            <section className="result-card">
              <div className="billing-cta">
                <strong>{result.billing_redirect.message}</strong>
                <p>{result.billing_redirect.recommended_offer}</p>
                <div className="checkout-stack" style={{ marginTop: 16 }}>
                  {result.billing_redirect.checkout_options.slice(0, 3).map((opt) => (
                    <button key={opt.code} onClick={() => startCheckout(opt.code)}>{opt.label}</button>
                  ))}
                </div>
              </div>
            </section>
          )}

          {humanizeResult?.billing_redirect && (
            <section className="result-card">
              <div className="billing-cta">
                <strong>{humanizeResult.billing_redirect.message}</strong>
                <p>{humanizeResult.billing_redirect.recommended_offer}</p>
                <div className="checkout-stack" style={{ marginTop: 16 }}>
                  {humanizeResult.billing_redirect.checkout_options.slice(0, 3).map((opt) => (
                    <button key={opt.code} onClick={() => startCheckout(opt.code)}>{opt.label}</button>
                  ))}
                </div>
              </div>
            </section>
          )}

        </main>
      )}
    </div>
  );
}
