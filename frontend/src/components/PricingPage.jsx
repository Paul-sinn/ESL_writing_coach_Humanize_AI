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
              ? "구독 취소 관리"
              : isDowngrade
                ? "다운그레이드 관리 →"
                : "업그레이드 →";

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
                  <div className="pricing-current-badge">현재 플랜</div>
                ) : isPlanChange ? (
                  <button
                    className={`pricing-upgrade-btn${plan.featured ? " pricing-upgrade-btn-primary" : ""}`}
                    onClick={() => onCheckout(plan.code)}
                    disabled={loading === plan.code}
                  >
                    {loading === plan.code ? "이동 중…" : actionLabel}
                  </button>
                ) : currentStatus === "free" && plan.statusKey === "free" ? (
                  <button className="pricing-upgrade-btn pricing-upgrade-btn-muted" onClick={onClose}>무료로 시작</button>
                ) : (
                  <div className="pricing-current-badge">현재 플랜</div>
                )}
              </div>
            );
          })}
        </div>

        <div className="pricing-packs-section">
          <h3>크레딧 팩 — 일회성 구매</h3>
          <p>구독 없이도 사용 가능. 크레딧 만료 없음.</p>
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
          이 서비스는 자연스러운 영어 작문을 돕는 코치입니다. AI 감지 우회나 Turnitin 회피를 보장하지 않습니다.
        </p>
      </div>
    </div>
  );
}
