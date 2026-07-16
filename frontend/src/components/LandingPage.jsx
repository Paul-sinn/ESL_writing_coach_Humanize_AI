import {
  motion,
  useMotionValue,
  useMotionTemplate,
  useAnimationFrame,
} from "framer-motion";

function GridPattern({ patternId, offsetX, offsetY }) {
  return (
    <svg style={{ width: "100%", height: "100%" }}>
      <defs>
        <motion.pattern
          id={patternId}
          width="40"
          height="40"
          patternUnits="userSpaceOnUse"
          x={offsetX}
          y={offsetY}
        >
          <path
            d="M 40 0 L 0 0 0 40"
            fill="none"
            stroke="currentColor"
            strokeWidth="1"
          />
        </motion.pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${patternId})`} />
    </svg>
  );
}

export default function LandingPage({ onStart, onUpgrade }) {
  const mouseX = useMotionValue(-9999);
  const mouseY = useMotionValue(-9999);

  const gridOffsetX = useMotionValue(0);
  const gridOffsetY = useMotionValue(0);

  const handleMouseMove = (e) => {
    const { left, top } = e.currentTarget.getBoundingClientRect();
    mouseX.set(e.clientX - left);
    mouseY.set(e.clientY - top);
  };

  const handleMouseLeave = () => {
    mouseX.set(-9999);
    mouseY.set(-9999);
  };

  useAnimationFrame(() => {
    gridOffsetX.set((gridOffsetX.get() + 0.4) % 40);
    gridOffsetY.set((gridOffsetY.get() + 0.4) % 40);
  });

  const maskImage = useMotionTemplate`radial-gradient(320px circle at ${mouseX}px ${mouseY}px, black, transparent)`;

  return (
    <div
      className="landing-root"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Base grid — always visible, very faint */}
      <div className="landing-grid-base">
        <GridPattern patternId="grid-base" offsetX={gridOffsetX} offsetY={gridOffsetY} />
      </div>

      {/* Spotlight grid — follows cursor */}
      <motion.div
        className="landing-grid-spotlight"
        style={{ maskImage, WebkitMaskImage: maskImage }}
      >
        <GridPattern patternId="grid-spotlight" offsetX={gridOffsetX} offsetY={gridOffsetY} />
      </motion.div>

      {/* Ambient glow blobs */}
      <div className="landing-blobs" aria-hidden="true">
        <div className="landing-blob landing-blob-orange" />
        <div className="landing-blob landing-blob-blue" />
        <div className="landing-blob landing-blob-accent" />
      </div>

      {/* Hero content */}
      <div className="landing-content">
        <motion.div
          className="landing-tag"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          ESL Academic Writing Coach
        </motion.div>

        <motion.h1
          className="landing-headline"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          Write clearer essays.
          <br />
          <span className="landing-headline-accent">Sound more human.</span>
        </motion.h1>

        <motion.p
          className="landing-sub"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          AI-powered coaching built for ESL college students.
          <br />
          Detect generic patterns, strengthen your voice, rewrite naturally.
        </motion.p>

        <motion.div
          className="landing-features"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          {[
            "AI pattern detection",
            "Personal voice coaching",
            "AI rewrite engine",
          ].map((f) => (
            <div key={f} className="landing-feature">
              <span className="landing-feature-dot" />
              {f}
            </div>
          ))}
        </motion.div>

        <motion.div
          className="landing-free-strip"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <span className="landing-free-check">✓</span>
          Free to start &nbsp;·&nbsp; 1 session / day &nbsp;·&nbsp; No credit card required
        </motion.div>

        <motion.div
          className="landing-actions"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.45 }}
        >
          <button className="landing-cta-btn" onClick={onStart}>
            Try it free
            <span className="landing-cta-arrow">→</span>
          </button>
          <button className="landing-secondary-btn" onClick={onUpgrade}>
            See pricing
          </button>
        </motion.div>

        {/* Social proof */}
        <motion.div
          className="landing-social-proof"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.6 }}
        >
          <div className="landing-avatars">
            {["K", "J", "M", "S", "A"].map((l) => (
              <div key={l} className="landing-avatar">{l}</div>
            ))}
          </div>
          <span className="landing-social-text">
            Trusted by 500+ international students
          </span>
        </motion.div>
      </div>

      {/* Floating stats cards */}
      <motion.div
        className="landing-stat-card landing-stat-card-left"
        initial={{ opacity: 0, x: -30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.7, delay: 0.7 }}
      >
        <div className="landing-stat-value">94%</div>
        <div className="landing-stat-label">Naturalness improvement</div>
      </motion.div>

      <motion.div
        className="landing-stat-card landing-stat-card-right"
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.7, delay: 0.8 }}
      >
        <div className="landing-stat-value">3x</div>
        <div className="landing-stat-label">Faster revision cycle</div>
      </motion.div>
    </div>
  );
}
