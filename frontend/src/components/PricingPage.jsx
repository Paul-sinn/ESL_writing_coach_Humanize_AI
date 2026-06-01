const PLANS = [
  {
    code: "free",
    statusKey: "free",
    name: "Free",
    price: 0,
    unit: "",
    credits: "300 words/day",
    features: ["1 analysis/day", "300 word limit", "Basic feedback"],
  },
  {
    code: "starter_monthly",
    statusKey: "starter",
    name: "Starter",
    price: 7,
    unit: "/mo",
    credits: "20,000 cr/mo",
    features: ["~10 deep analyses/mo", "1,200 word limit", "All feedback types", "Humanize tool"],
  },
  {
    code: "student_plus_monthly",
    statusKey: "student_plus",
    name: "Student Plus",
    price: 12,
    unit: "/mo",
    credits: "60,000 cr/mo",
    features: ["~30 deep analyses/mo", "1,200 word limit", "All feedback + Humanize", "Priority support"],
    featured: true,
  },
  {
    code: "pro_monthly",
    statusKey: "pro",
    name: "Pro",
    price: 19,
    unit: "/mo",
    credits: "150,000 cr/mo",
    features: ["~75 deep analyses/mo", "1,200 word limit", "All feedback + Humanize", "Priority support"],
  },
];

const CREDIT_PACKS = [
  { code: "credit_pack_s", label: "$5", credits: "25,000 credits", note: "≈12 deep analyses" },
  { code: "credit_pack_m", label: "$10", credits: "60,000 credits", note: "≈30 deep analyses" },
  { code: "credit_pack_l", label: "$20", credits: "150,000 credits", note: "≈75 deep analyses" },
];

const PLAN_ORDER = ["free", "starter", "student_plus", "pro"];

export default function PricingPage({ onClose, onCheckout, currentStatus, loading }) {
  const currentIdx = PLAN_ORDER.indexOf(currentStatus ?? "free");

  return (
    <div className="pricing-overlay" onClick={onClose}>
      <div className="pricing-sheet" onClick={(e) => e.stopPropagation()}>
        <button className="pricing-close" onClick={onClose}>✕</button>

        <div className="pricing-header">
          <div className="eyebrow">Pricing</div>
          <h2>Choose your plan</h2>
          <p>Credits roll over while you stay subscribed.</p>
        </div>

        <div className="pricing-grid">
          {PLANS.map((plan) => {
            const isCurrent = plan.statusKey === (currentStatus ?? "free");
            const planIdx = PLAN_ORDER.indexOf(plan.statusKey);
            const isDowngrade = planIdx < currentIdx;
            const isPlanChange = !isCurrent;
            const actionLabel = plan.statusKey === "free"
              ? "Manage subscription"
              : isDowngrade
                ? "Manage downgrade →"
                : "Upgrade →";

            return (
              <div key={plan.name} className={`pricing-card${plan.featured ? " pricing-card-featured" : ""}`}>
                {plan.featured && <div className="pricing-badge-pop">Most Popular</div>}

                <div className="pricing-card-name">{plan.name}</div>
                <div className="pricing-card-price">
                  ${plan.price}<span className="pricing-card-unit">{plan.unit}</span>
                </div>
                <div className="pricing-card-credits">{plan.credits}</div>

                <ul className="pricing-card-features">
                  {plan.features.map((f) => (
                    <li key={f}><span className="pricing-feat-check">✓</span>{f}</li>
                  ))}
                </ul>

                {isCurrent ? (
                  <div className="pricing-current-badge">Current plan</div>
                ) : isPlanChange ? (
                  <button
                    className={`pricing-upgrade-btn${plan.featured ? " pricing-upgrade-btn-primary" : ""}`}
                    onClick={() => onCheckout(plan.code)}
                    disabled={loading === plan.code}
                  >
                    {loading === plan.code ? "Redirecting…" : actionLabel}
                  </button>
                ) : currentStatus === "free" && plan.statusKey === "free" ? (
                  <button className="pricing-upgrade-btn pricing-upgrade-btn-muted" onClick={onClose}>Start for free</button>
                ) : (
                  <div className="pricing-current-badge">Current plan</div>
                )}
              </div>
            );
          })}
        </div>

        <div className="pricing-packs-section">
          <h3>Credit packs — one-time purchase</h3>
          <p>Use them without a subscription. Credits do not expire.</p>
          <div className="pricing-packs-row">
            {CREDIT_PACKS.map((pack) => (
              <button
                key={pack.code}
                className="pricing-pack-btn"
                onClick={() => onCheckout(pack.code)}
                disabled={loading === pack.code}
              >
                <span className="pricing-pack-price">{pack.label}</span>
                <span className="pricing-pack-credits">{pack.credits}</span>
                <span className="pricing-pack-note">{pack.note}</span>
              </button>
            ))}
          </div>
        </div>

        <p className="pricing-disclaimer">
          This service coaches clearer, more natural English writing. It does not guarantee AI detector or Turnitin bypass.
        </p>
      </div>
    </div>
  );
}
