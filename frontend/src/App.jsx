import { useEffect, useState } from "react";

const WORD_LIMIT = 1200;
const FREE_WORD_LIMIT = 300;

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
  { value: "basic", label: "Quick Check", costPerWord: 1, description: "Top 3 issues" },
  { value: "deep", label: "Deep Feedback", costPerWord: 2, description: "Full analysis + suggestions" },
  { value: "full_review", label: "Full Review", costPerWord: 5, description: "Everything + example rewrites" },
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

const ISSUE_LABELS = {
  ai_pattern: "AI Writing Pattern",
  unnatural_english: "Unnatural English",
  robotic_tone: "Robotic Tone",
  missing_example: "Missing Personal Voice",
  clarity_issue: "Clarity",
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

function countWords(text) {
  const matches = text.trim().match(/\b[\w'-]+\b/g);
  return matches ? matches.length : 0;
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
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
  const [text, setText] = useState("");
  const [assignmentType, setAssignmentType] = useState("general_academic");
  const [writingLevel, setWritingLevel] = useState("intermediate");
  const [depth, setDepth] = useState("deep");
  const [result, setResult] = useState(null);
  const [billing, setBilling] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [pwCurrent, setPwCurrent] = useState("");
  const [pwNew, setPwNew] = useState("");
  const [pwConfirm, setPwConfirm] = useState("");
  const [pwMessage, setPwMessage] = useState(null);
  const [humanizeResult, setHumanizeResult] = useState(null);
  const [humanizeLoading, setHumanizeLoading] = useState(false);
  const [showHumanizeModal, setShowHumanizeModal] = useState(false);
  const [humanizeTone, setHumanizeTone] = useState("natural_student");
  const [humanizeStrength, setHumanizeStrength] = useState("balanced");
  const [preserveMeaning, setPreserveMeaning] = useState(true);
  const [preserveCitations, setPreserveCitations] = useState(false);
  const [preserveStructure, setPreserveStructure] = useState(false);

  const wordCount = countWords(text);
  const overLimit = wordCount > WORD_LIMIT;
  const isFreePlan = billing?.subscription_status === "free";
  const freeLimitWarning = isFreePlan && wordCount > FREE_WORD_LIMIT;

  const selectedDepth = DEPTH_OPTIONS.find((d) => d.value === depth);
  const estimatedCost = isFreePlan ? 0 : wordCount * (selectedDepth?.costPerWord ?? 2);
  const canSubmit = text.trim() && !overLimit && !loading;

  useEffect(() => {
    fetchJson("/api/billing/status")
      .then(setBilling)
      .catch(() => setBilling(null));
  }, []);

  async function handleCoach() {
    setLoading(true);
    setError("");
    setResult(null);
    setHumanizeResult(null);
    try {
      const data = await fetchJson("/api/coach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          assignment_type: assignmentType,
          writing_level: writingLevel,
          depth,
        }),
      });
      setResult(data);
      if (data.billing_redirect) {
        setError(data.billing_redirect.message);
      }
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
          preserve_meaning: preserveMeaning,
          preserve_citations: preserveCitations,
          preserve_structure: preserveStructure,
        }),
      });
      setHumanizeResult(data);
      if (data.billing_redirect) {
        setError(data.billing_redirect.message);
      }
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

  function handleChangePassword(e) {
    e.preventDefault();
    if (!pwCurrent || !pwNew || !pwConfirm) {
      setPwMessage({ type: "error", text: "모든 항목을 입력해주세요." });
      return;
    }
    if (pwNew !== pwConfirm) {
      setPwMessage({ type: "error", text: "새 비밀번호가 일치하지 않습니다." });
      return;
    }
    if (pwNew.length < 8) {
      setPwMessage({ type: "error", text: "비밀번호는 최소 8자 이상이어야 합니다." });
      return;
    }
    setPwMessage({ type: "success", text: "비밀번호가 변경되었습니다." });
    setPwCurrent(""); setPwNew(""); setPwConfirm("");
  }

  const planInitial = (billing?.plan_name ?? "F")[0].toUpperCase();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">WC</div>
          <div>
            <div className="brand-name">Writing Coach</div>
            <div className="brand-subtitle">ESL Academic Writing Assistant</div>
          </div>
        </div>
        <nav className="topnav">
          <a className="nav-link active" href="#workspace">Coach</a>
          <a className="nav-link" href="#billing">Pricing</a>
          <button className="topnav-cta" onClick={() => startCheckout("student_plus_monthly")}>
            Upgrade to Student Plus
          </button>
          <button
            className="profile-avatar-btn"
            onClick={() => { setProfileOpen(true); setPwMessage(null); }}
            aria-label="Profile"
          >
            <span>{planInitial}</span>
          </button>
        </nav>
      </header>

      {profileOpen && (
        <div className="profile-overlay" onClick={() => setProfileOpen(false)}>
          <div className="profile-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="profile-drawer-header">
              <div className="profile-avatar-large">{planInitial}</div>
              <div className="profile-header-info">
                <div className="profile-name">My Account</div>
                <div className={`profile-mode-badge ${billing?.subscription_status ?? "free"}`}>
                  {billing?.plan_name ?? "Free"} Plan
                </div>
              </div>
              <button className="profile-close-btn" onClick={() => setProfileOpen(false)} aria-label="Close">✕</button>
            </div>

            <div className="profile-section">
              <div className="profile-section-label">Credits</div>
              <div className="profile-credits-row">
                <div className="profile-credits-display">
                  <span className="profile-credits-number">{billing?.credits_remaining?.toLocaleString() ?? 0}</span>
                  <span className="profile-credits-unit">credits remaining</span>
                </div>
                <div className="profile-credits-actions">
                  <button className="secondary profile-recharge-btn" onClick={() => startCheckout("credit_pack_s")}>+$5</button>
                  <button className="secondary profile-recharge-btn" onClick={() => startCheckout("credit_pack_m")}>+$10</button>
                  <button className="secondary profile-recharge-btn" onClick={() => startCheckout("credit_pack_l")}>+$20</button>
                </div>
              </div>
              {billing?.subscription_status === "free" && (
                <button className="profile-upgrade-btn" onClick={() => startCheckout("student_plus_monthly")}>
                  Upgrade to Student Plus · $12/month
                </button>
              )}
            </div>

            <div className="profile-divider" />

            <div className="profile-section">
              <div className="profile-section-label">Change Password</div>
              <form className="profile-pw-form" onSubmit={handleChangePassword}>
                <input type="password" placeholder="현재 비밀번호" value={pwCurrent}
                  onChange={(e) => { setPwCurrent(e.target.value); setPwMessage(null); }}
                  autoComplete="current-password" />
                <input type="password" placeholder="새 비밀번호 (8자 이상)" value={pwNew}
                  onChange={(e) => { setPwNew(e.target.value); setPwMessage(null); }}
                  autoComplete="new-password" />
                <input type="password" placeholder="새 비밀번호 확인" value={pwConfirm}
                  onChange={(e) => { setPwConfirm(e.target.value); setPwMessage(null); }}
                  autoComplete="new-password" />
                {pwMessage && <div className={`profile-pw-msg ${pwMessage.type}`}>{pwMessage.text}</div>}
                <button type="submit" className="profile-pw-submit">비밀번호 변경</button>
              </form>
            </div>
          </div>
        </div>
      )}

      {showHumanizeModal && (
        <div className="humanize-modal-overlay" onClick={() => setShowHumanizeModal(false)}>
          <div className="humanize-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Humanize Options</h3>

            <div className="option-group">
              <div className="option-label">Tone</div>
              <div className="toggle-row">
                {TONE_OPTIONS.map((t) => (
                  <button
                    key={t.value}
                    className={`toggle-btn ${humanizeTone === t.value ? "active" : ""}`}
                    onClick={() => setHumanizeTone(t.value)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="option-group">
              <div className="option-label">Strength</div>
              <div className="toggle-row">
                {STRENGTH_OPTIONS.map((s) => (
                  <button
                    key={s.value}
                    className={`toggle-btn ${humanizeStrength === s.value ? "active" : ""}`}
                    onClick={() => setHumanizeStrength(s.value)}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="option-group">
              <div className="option-label">Preserve</div>
              <div className="preserve-row">
                <label>
                  <input type="checkbox" checked={preserveMeaning}
                    onChange={(e) => setPreserveMeaning(e.target.checked)} />
                  Original meaning
                </label>
                <label>
                  <input type="checkbox" checked={preserveCitations}
                    onChange={(e) => setPreserveCitations(e.target.checked)} />
                  Citations
                </label>
                <label>
                  <input type="checkbox" checked={preserveStructure}
                    onChange={(e) => setPreserveStructure(e.target.checked)} />
                  Structure
                </label>
              </div>
            </div>

            <div className="modal-actions">
              <button className="secondary" onClick={() => setShowHumanizeModal(false)}>Cancel</button>
              <button onClick={handleHumanize}>Run Humanize →</button>
            </div>
          </div>
        </div>
      )}

      <main className="workspace" id="workspace">
        <section className="hero-panel">
          <div className="hero-copy">
            <div className="eyebrow">ESL Writing Coach</div>
            <h1>Write clearer academic English in your own voice.</h1>
            <p>
              Get personalized feedback on your essays, discussion posts, and academic writing.
              Find generic phrases, improve natural English, and strengthen your personal voice.
            </p>
            <div className="hero-stats">
              <div className="hero-stat">
                <strong>Free</strong>
                <span>1 check/day · 300 words</span>
              </div>
              <div className="hero-stat">
                <strong>$12/mo</strong>
                <span>Student Plus · 60K credits</span>
              </div>
              <div className="hero-stat">
                <strong>5 agents</strong>
                <span>policy → analyze → coach → revise → integrity</span>
              </div>
            </div>
          </div>

          <div className="billing-panel" id="billing">
            <div className="eyebrow">Pricing</div>
            <h2>Start free. Upgrade when you're ready.</h2>
            <p className="muted">Free: 1 analysis/day, 300 words. Paid plans unlock deeper feedback and longer essays.</p>
            <div className="balance-card">
              <span>Plan</span>
              <strong>{billing?.plan_name ?? "Free"}</strong>
              <span>Credits</span>
              <strong>{billing?.credits_remaining?.toLocaleString() ?? 0}</strong>
            </div>
            <div className="checkout-stack">
              <button onClick={() => startCheckout("starter_monthly")}>Starter · $7/month · 20K credits</button>
              <button onClick={() => startCheckout("student_plus_monthly")}>
                Student Plus · $12/month · 60K credits
              </button>
              <button className="secondary" onClick={() => startCheckout("credit_pack_s")}>Buy $5 credits (25K)</button>
              <button className="secondary" onClick={() => startCheckout("credit_pack_m")}>Buy $10 credits (60K)</button>
            </div>
          </div>
        </section>

        <section className="editor-card">
          <div className="editor-toolbar">
            <div>
              <div className="eyebrow">Workspace</div>
              <h2>Paste your essay and get coaching feedback.</h2>
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
                rows={16}
              />
              <div className={`word-counter ${overLimit ? "danger" : ""}`}>
                {wordCount} / {WORD_LIMIT} words
                {isFreePlan && !overLimit && (
                  <span className="free-limit-note"> · Free plan: {FREE_WORD_LIMIT} word max</span>
                )}
              </div>
              {overLimit && <div className="inline-error">Over the 1,200-word limit.</div>}
              {freeLimitWarning && !overLimit && (
                <div className="inline-error">Free plan is limited to {FREE_WORD_LIMIT} words. Upgrade to analyze longer essays.</div>
              )}
            </div>

            <div className="requirements-card">
              <div className="requirements-header">
                <div>
                  <h3>Coaching Options</h3>
                  <p>Select your assignment type, level, and how deep you'd like the feedback.</p>
                </div>
              </div>

              <div className="coach-selects">
                <div className="select-group">
                  <label className="select-label">Assignment Type</label>
                  <select
                    className="coach-select"
                    value={assignmentType}
                    onChange={(e) => setAssignmentType(e.target.value)}
                  >
                    {ASSIGNMENT_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>

                <div className="select-group">
                  <label className="select-label">Writing Level</label>
                  <select
                    className="coach-select"
                    value={writingLevel}
                    onChange={(e) => setWritingLevel(e.target.value)}
                  >
                    {WRITING_LEVELS.map((l) => (
                      <option key={l.value} value={l.value}>{l.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="depth-row">
                {DEPTH_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    className={`depth-btn ${depth === opt.value ? "active" : ""}`}
                    onClick={() => setDepth(opt.value)}
                  >
                    <span className="depth-name">{opt.label}</span>
                    <span className="depth-desc">{opt.description}</span>
                    <span className="depth-cost">
                      {isFreePlan ? (opt.value === "basic" ? "Free" : "Paid") : `~${(wordCount * opt.costPerWord).toLocaleString()} cr`}
                    </span>
                  </button>
                ))}
              </div>

              {!isFreePlan && wordCount > 0 && (
                <div className="cost-estimate">
                  Estimated cost: <strong>{estimatedCost.toLocaleString()} credits</strong>
                  {" · "}
                  <span className="muted">{billing?.credits_remaining?.toLocaleString() ?? 0} remaining</span>
                </div>
              )}

              <div className="action-row">
                <button disabled={!canSubmit} onClick={handleCoach}>
                  {loading ? "Analyzing..." : "Get Feedback"}
                </button>
              </div>
            </div>
          </div>

          {error && <div className="inline-error inline-banner">{error}</div>}
        </section>

        {result && !result.billing_redirect && (
          <section className="result-card" id="results">
            <div className="result-header">
              <div>
                <div className="eyebrow">Writing Analysis</div>
                <h2>Your Writing Scores</h2>
              </div>
              <div className={`verdict ${result.verdict_label}`}>
                {result.verdict_label === "high"
                  ? "High AI-like"
                  : result.verdict_label === "medium"
                  ? "Some AI patterns"
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
                  {result.signals.map((s, i) => (
                    <span key={i}>{s}</span>
                  ))}
                </div>
              </div>
            )}

            {result.strengths.length > 0 && (
              <div className="strengths-section">
                <div className="strengths-label">What's working well</div>
                <div className="signal-list">
                  {result.strengths.map((s, i) => (
                    <span key={i} className="strength-chip">{s}</span>
                  ))}
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

            <button
              className="humanize-cta"
              onClick={() => setShowHumanizeModal(true)}
              disabled={humanizeLoading}
            >
              <span className="humanize-cta-title">
                {humanizeLoading ? "Humanizing..." : "✦ Humanize Full Essay"}
              </span>
              <span className="humanize-cta-sub">
                Rewrite for clarity and voice · ~{(result.input_word_count * 3).toLocaleString()} credits
              </span>
            </button>

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
          <section className="result-card">
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
                  {humanizeResult.key_improvements.map((imp, i) => (
                    <li key={i}>{imp}</li>
                  ))}
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
                  <button key={opt.code} onClick={() => startCheckout(opt.code)}>
                    {opt.label}
                  </button>
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
                  <button key={opt.code} onClick={() => startCheckout(opt.code)}>
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
