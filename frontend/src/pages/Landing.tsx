import "./../styles/landing.css";

export const Landing = () => (
  <main className="landing">
    <section className="hero">
      <p className="eyebrow">AI-FIRST MARKET COPILOT</p>
      <h1>Finbot helps you move from signal to trade in seconds.</h1>
      <p className="subhead">
        Real-time market data, compliance-ready AI insights, and automated workflows designed for Indian
        investors.
      </p>
      <div className="cta-row">
        <a className="btn primary" href="/register">
          Get Started
        </a>
        <a className="btn ghost" href="/demo">
          Watch Demo
        </a>
      </div>
    </section>
    <section className="features">
      <article>
        <h3>&lt;150ms API</h3>
        <p>Optimized FastAPI backend with Redis caching and observability.</p>
      </article>
      <article>
        <h3>Safety-first AI</h3>
        <p>Hallucination guardrails with prompt moderation and evidence tracking.</p>
      </article>
      <article>
        <h3>Compliance-ready</h3>
        <p>DPDP + SEBI documentation, encryption in transit and at rest.</p>
      </article>
    </section>
  </main>
);

export default Landing;
