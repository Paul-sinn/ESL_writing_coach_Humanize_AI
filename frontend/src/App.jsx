import { useEffect, useRef, useState } from "react";

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
  { value: "full_review", label: "Full Review", costPerWord: 5, minCredits: 3000, description: "Everything + rewrites" },
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
  const token = localStorage.getItem("token");
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
    throw new Error(data?.detail || data?.message || `Request failed for ${path}.`);
  }
  return data;
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
  const [showEditor, setShowEditor] = useState(() => localStorage.getItem("showEditor") === "true");

  useEffect(() => {
    localStorage.setItem("showEditor", showEditor);
  }, [showEditor]);
  const [text, setText] = useState("");
  const [assignmentType, setAssignmentType] = useState("general_academic");
  const [writingLevel, setWritingLevel] = useState("intermediate");
  const [depth, setDepth] = useState("deep");
  const [result, setResult] = useState(null);
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
  const [currentUser, setCurrentUser] = useState(() => {
    const token = localStorage.getItem("token");
    const email = localStorage.getItem("userEmail");
    const username = localStorage.getItem("userUsername");
    const nickname = localStorage.getItem("userNickname");
    return token ? { token, email, username, nickname } : null;
  });
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState("login"); // "login" | "register" | "verify"
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

  useEffect(() => {
    localStorage.setItem("darkMode", darkMode);
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

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

  const selectedDepth = DEPTH_OPTIONS.find((d) => d.value === depth);
  const feedbackCost = isFreePlan ? 0 : Math.max(
    wordCount * (selectedDepth?.costPerWord ?? 2),
    selectedDepth?.minCredits ?? 1200,
  );
  const humanizeCost = isFreePlan ? 0 : Math.max(wordCount * HUMANIZE_COST_PER_WORD, HUMANIZE_MIN_CREDITS);
  const canSubmit = text.trim() && !overLimit && !loading && !humanizeLoading;

  useEffect(() => {
    fetchJson("/api/billing/status")
      .then(setBilling)
      .catch(() => setBilling(null));
  }, []);

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
      setCoachFeedback(data.feedback_items?.length ? data.feedback_items : null);
      if (data.billing_redirect) setError(data.billing_redirect.message);
      setBilling(await fetchJson("/api/billing/status"));
    } catch (err) {
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
      if (data.billing_redirect) setError(data.billing_redirect.message);
      setBilling(await fetchJson("/api/billing/status"));
    } catch (err) {
      setError(err.message);
    } finally {
      setHumanizeLoading(false);
    }
  }

  async function startCheckout(productCode) {
    try {
      const data = await fetchJson("/api/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_code: productCode }),
      });
      window.open(data.checkout_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err.message);
    }
  }


  function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("userEmail");
    localStorage.removeItem("userUsername");
    localStorage.removeItem("userNickname");
    setCurrentUser(null);
    setProfileOpen(false);
    setBilling(null);
    fetchJson("/api/billing/status").then(setBilling).catch(() => {});
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

  async function checkEmail() {
    if (!authEmail) return;
    setEmailChecking(true);
    try {
      const data = await fetchJson(`/api/auth/check-email?email=${encodeURIComponent(authEmail)}`);
      setEmailAvail(data.available);
    } catch { setEmailAvail(false); }
    finally { setEmailChecking(false); }
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
      const data = await fetchJson("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email: authEmail, username: authUsername, nickname: authUsername, password: authPassword, password_confirm: authPasswordConfirm }),
      });
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("userEmail", data.email);
      localStorage.setItem("userUsername", data.username ?? "");
      localStorage.setItem("userNickname", data.nickname ?? "");
      setCurrentUser({ token: data.access_token, email: data.email, username: data.username, nickname: data.nickname });
      setShowAuthModal(false);
      setBilling(await fetchJson("/api/billing/status"));
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
      const data = await fetchJson("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("userEmail", data.email);
      localStorage.setItem("userUsername", data.username ?? "");
      localStorage.setItem("userNickname", data.nickname ?? "");
      setCurrentUser({ token: data.access_token, email: data.email, username: data.username, nickname: data.nickname });
      setShowAuthModal(false);
      setBilling(await fetchJson("/api/billing/status"));
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  const planInitial = currentUser
    ? currentUser.email[0].toUpperCase()
    : (billing?.plan_name ?? "F")[0].toUpperCase();

  return (
    <div className="app-shell">
      <header className="topbar">
        <button
          className="brand-lockup brand-home-btn"
          onClick={() => setShowEditor(false)}
          aria-label="Home"
        >
          <div className="brand-mark">WC</div>
          <div>
            <div className="brand-name">Writing Coach</div>
            <div className="brand-subtitle">ESL Academic Writing Assistant</div>
          </div>
        </button>
        <nav className="topnav">
          {billing && !isFreePlan && (
            <div className={`nav-credits ${
              billing.credits_remaining < 1000 ? "nav-credits-critical" :
              billing.credits_remaining < 5000 ? "nav-credits-low" : ""
            }`}>
              ⚡ {billing.credits_remaining.toLocaleString()} cr
            </div>
          )}
          <button className="topnav-cta" onClick={() => setShowUpgradeModal(true)}>
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
                {currentUser ? (
                  <div className="pd-account-row">
                    <div>
                      <div className="pd-user-nickname">{currentUser.nickname || currentUser.email}</div>
                      <div className="pd-user-handle">@{currentUser.username || ""}</div>
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
                {currentUser ? (
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
      </header>

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

            {authMode === "register" && (
              <>
                <div className="auth-modal-header">
                  <h3>Create account</h3>
                  <p>Start coaching your ESL academic writing for free.</p>
                </div>
                <form onSubmit={handleRegister}>
                  <div className="auth-field">
                    <label>Email</label>
                    <div className="auth-check-row">
                      <input type="email" value={authEmail} onChange={(e) => { setAuthEmail(e.target.value); setEmailAvail(null); }} placeholder="you@email.com" required autoFocus />
                      <button type="button" className="auth-check-btn" onClick={checkEmail} disabled={!authEmail || emailChecking}>
                        {emailChecking ? "…" : "Check"}
                      </button>
                    </div>
                    {emailAvail === true && <div className="auth-avail-ok">✓ Email is available</div>}
                    {emailAvail === false && <div className="auth-avail-fail">✗ Email is already in use</div>}
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
                  <button type="submit" className="auth-submit-btn" disabled={authLoading || emailAvail !== true || usernameAvail !== true || !tosAgreed}>
                    {authLoading ? "Creating account…" : "Create account →"}
                  </button>
                  {(emailAvail !== true || usernameAvail !== true) && !authLoading && (
                    <div className="auth-check-hint">Please check availability for email and username</div>
                  )}
                </form>
                <div className="auth-switch">
                  Already have an account?{" "}
                  <button type="button" className="auth-link" onClick={() => openAuth("login")}>Log in</button>
                </div>
              </>
            )}

            {authMode === "login" && (
              <>
                <div className="auth-modal-header">
                  <h3>Welcome back</h3>
                  <p>Log in to your Writing Coach account.</p>
                </div>
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
        <main className="hero-page">
          <div className="hero-blobs" aria-hidden="true">
            <div className="blob blob-1" />
            <div className="blob blob-2" />
            <div className="blob blob-3" />
            <div className="blob blob-4" />
          </div>

          <div className="hero-glass">
            <div className="hero-tag">ESL Academic Writing Coach</div>

            <h1 className="hero-headline">
              Write clearer essays.<br />
              <span className="hero-headline-accent">Sound more human.</span>
            </h1>

            <p className="hero-sub">
              Get AI-powered coaching on your academic writing.<br></br>
              Detect generic patterns, improve your voice, and rewrite in natural English.
            </p>

            <div className="hero-features">
              <div className="hero-feature">
                <span className="hero-feature-icon">◎</span>
                AI pattern detection
              </div>
              <div className="hero-feature">
                <span className="hero-feature-icon">◎</span>
                Personal voice coaching
              </div>
              <div className="hero-feature">
                <span className="hero-feature-icon">◎</span>
                Humanize rewrite engine
              </div>
            </div>

            <div className="hero-free-strip">
              <span className="hero-free-check">✓</span>
              Free to start &nbsp;·&nbsp; 1 coaching session per day &nbsp;·&nbsp; No credit card required
            </div>

            <button className="hero-cta-btn" onClick={() => setShowEditor(true)}>
              Try it free
              <span className="hero-cta-arrow">→</span>
            </button>
          </div>
        </main>
      )}

      {/* ── Editor page ── */}
      {showEditor && (
        <main className="workspace">

          <section className="editor-card">
            <div className="editor-toolbar">
              <div>
                <div className="eyebrow">Workspace</div>
                <h2>Paste your essay below.</h2>
              </div>
              {billing && (
                <div className="editor-balance">
                  <span className="editor-plan-badge">{billing.plan_name}</span>
                  <span className="editor-credits">{billing.credits_remaining?.toLocaleString()} cr</span>
                </div>
              )}
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
              <div className="result-header">
                <div>
                  <div className="eyebrow">Writing Analysis</div>
                  <h2>Your Writing Scores</h2>
                </div>
                <div className={`verdict ${result.verdict_label}`}>
                  {result.verdict_label === "high" ? "High AI-like"
                    : result.verdict_label === "medium" ? "Some AI patterns"
                    : "Mostly Human"}
                </div>
              </div>

              <div className="score-grid">
                <ScoreCard label="AI-Like Writing" score={result.ai_like_score} invert />
                <ScoreCard label="Naturalness" score={result.naturalness_score} />
                <ScoreCard label="Personal Voice" score={result.personal_voice_score} />
                <ScoreCard label="Clarity" score={result.clarity_score} />
              </div>

              <p className="result-summary-text">{result.overall_summary}</p>

              {result.signals?.length > 0 && (
                <div className="signal-section">
                  <div className="signal-section-label">Detected Patterns</div>
                  <div className="signal-list">
                    {result.signals.map((s, i) => <span key={i}>{s}</span>)}
                  </div>
                </div>
              )}

              {result.strengths.length > 0 && (
                <div className="strengths-section">
                  <div className="strengths-label">What's working well</div>
                  <div className="signal-list">
                    {result.strengths.map((s, i) => <span key={i} className="strength-chip">{s}</span>)}
                  </div>
                </div>
              )}

              {result.feedback_items.length > 0 && (
                <div className="feedback-list">
                  <div className="feedback-list-label">Writing Issues</div>
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
                </div>
              )}

              <p className="disclaimer-text">
                These scores are writing-pattern estimates, not guaranteed AI detector results.
                Always follow your school's academic integrity policy.
              </p>

              <div className="integrity-card">
                <div className="integrity-label">Academic Integrity</div>
                <p>{result.integrity_note}</p>
                <div className="disclosure-box">{result.disclosure_statement}</div>
              </div>

              <div className="credits-footer">
                Credits used: <strong>{result.credits_charged}</strong>
                {" · "}
                Remaining: <strong>{result.credits_remaining.toLocaleString()}</strong>
              </div>
            </section>
          )}

          {humanizeLoading && (
            <section className="result-card">
              <div className="humanize-loading">Humanizing your essay...</div>
            </section>
          )}

          {humanizeResult && !humanizeResult.billing_redirect && (
            <section className="result-card" ref={humanizeResultRef}>
              <div className="result-header">
                <div>
                  <div className="eyebrow">Humanized</div>
                  <h2>{humanizeResult.summary_of_changes}</h2>
                </div>
                <div className="verdict humanized">Rewritten</div>
              </div>
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
                <div className="improvements-list">
                  <div className="improvements-label">Key improvements</div>
                  <ul>
                    {humanizeResult.key_improvements.map((imp, i) => <li key={i}>{imp}</li>)}
                  </ul>
                </div>
              )}
              <div className="credits-footer">
                Credits used: <strong>{humanizeResult.credits_charged}</strong>
                {" · "}
                Remaining: <strong>{humanizeResult.credits_remaining.toLocaleString()}</strong>
              </div>
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
