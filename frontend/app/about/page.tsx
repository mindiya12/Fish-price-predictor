import Link from "next/link";
import { ArrowLeft, Brain, Database, TrendingUp, Shield, Clock, Globe, Mail, Github } from "lucide-react";

export default function AboutPage() {
  return (
    <div style={{ position: 'relative', zIndex: 1, maxWidth: '960px', margin: '0 auto', padding: '2rem 1.5rem 4rem' }}>
      
      {/* ── PAGE HEADER ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '3rem' }}>
        <div>
          {/* Badge */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', background: 'rgba(16, 217, 160, 0.08)', border: '1px solid rgba(16, 217, 160, 0.2)', borderRadius: '999px', padding: '0.3rem 0.875rem' }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10D9A0', boxShadow: '0 0 8px #10D9A0' }} />
            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#10D9A0', letterSpacing: '0.08em', textTransform: 'uppercase' }}>About the Project</span>
          </div>
          <h1 style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontSize: 'clamp(2rem, 5vw, 2.75rem)', fontWeight: 800, margin: '0 0 0.75rem', color: '#EDF4FF', lineHeight: 1.15 }}>
            About{' '}
            <span style={{ background: 'linear-gradient(135deg, #00D4FF, #10D9A0)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
              FishPrice.LK
            </span>
          </h1>
          <p style={{ color: '#7A9CC9', fontSize: '1rem', lineHeight: 1.7, maxWidth: '520px' }}>
            AI-powered fish price forecasting for Sri Lanka's wholesale markets — helping buyers, sellers, and researchers make smarter decisions.
          </p>
        </div>

        <Link
          href="/"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
            padding: '0.5rem 1rem', borderRadius: '0.625rem',
            fontSize: '0.85rem', fontWeight: 500,
            color: '#7A9CC9', background: 'rgba(100, 180, 255, 0.06)',
            border: '1px solid rgba(100, 180, 255, 0.1)',
            textDecoration: 'none', transition: 'all 0.2s',
            flexShrink: 0, marginTop: '1rem',
          }}
        >
          <ArrowLeft size={14} /> Back to Home
        </Link>
      </div>

      {/* ── DIVIDER ── */}
      <div className="divider" style={{ marginBottom: '3rem' }} />

      {/* ── MISSION SECTION ── */}
      <section className="glass" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(0, 212, 255, 0.1)', border: '1px solid rgba(0, 212, 255, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Brain size={20} color="#00D4FF" />
          </div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: '#EDF4FF' }}>What Is FishPrice.LK?</h2>
        </div>
        <p style={{ color: '#7A9CC9', fontSize: '0.9rem', lineHeight: 1.85, margin: '0 0 1rem' }}>
          FishPrice.LK is a machine-learning powered platform that predicts wholesale fish prices at the{' '}
          <span style={{ color: '#00D4FF' }}>Peliyagoda Fish Market</span> in Sri Lanka. Our ensemble model —
          combining XGBoost and LightGBM — is trained on over 9 years of historical price data, retraining
          daily to deliver the most accurate 3-day forecast available.
        </p>
        <p style={{ color: '#7A9CC9', fontSize: '0.9rem', lineHeight: 1.85, margin: 0 }}>
          Whether you're a wholesale buyer planning inventory, a retailer managing margins, or a researcher
          studying food price dynamics, FishPrice.LK gives you a data-driven edge.
        </p>
      </section>

      {/* ── FEATURES GRID ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {[
          {
            icon: TrendingUp, color: '#00D4FF',
            title: 'Multi-Horizon Forecast',
            desc: '3-day price predictions with confidence bands for Day 1, Day 2, and Day 3 horizons, each with its own model tuned for accuracy.',
          },
          {
            icon: Database, color: '#10D9A0',
            title: 'Rich Data Sources',
            desc: 'Price data sourced from CBSL daily market reports. Updated every morning at 5 AM LKT before markets open.',
          },
          {
            icon: Shield, color: '#FFB340',
            title: 'Uncertainty Quantification',
            desc: 'Every forecast ships with lower/upper confidence bounds so you can plan around best-case and worst-case pricing scenarios.',
          },
          {
            icon: Clock, color: '#A78BFA',
            title: 'Daily Retraining',
            desc: 'Model parameters refresh daily with the latest market data via automated GitHub Actions pipelines — no stale models.',
          },
        ].map(({ icon: Icon, color, title, desc }) => (
          <div key={title} className="glass glass-hover" style={{ padding: '1.5rem' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: `${color}15`, border: `1px solid ${color}25`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <Icon size={18} color={color} />
            </div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem', color: '#EDF4FF' }}>{title}</h3>
            <p style={{ fontSize: '0.82rem', color: '#4A6285', lineHeight: 1.75, margin: 0 }}>{desc}</p>
          </div>
        ))}
      </div>

      {/* ── MODEL PERFORMANCE ── */}
      <section className="glass" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(16, 217, 160, 0.1)', border: '1px solid rgba(16, 217, 160, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <TrendingUp size={20} color="#10D9A0" />
          </div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: '#EDF4FF' }}>Model Performance</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          {[
            { label: 'Day 1 RMSE', value: '26.31', sub: 'Root Mean Sq Error', color: '#00D4FF' },
            { label: 'Day 1 MAE', value: '23.82', sub: 'Mean Abs Error (Rs)', color: '#10D9A0' },
            { label: 'Day 1 R²', value: '0.85', sub: 'Variance explained', color: '#A78BFA' },
          ].map(({ label, value, sub, color }) => (
            <div key={label} style={{ textAlign: 'center', padding: '1.25rem', borderRadius: '0.75rem', background: `${color}08`, border: `1px solid ${color}18` }}>
              <p style={{ fontSize: '0.7rem', fontWeight: 600, color: '#4A6285', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.5rem' }}>{label}</p>
              <p style={{ fontSize: '1.75rem', fontWeight: 800, color, lineHeight: 1, marginBottom: '0.375rem' }}>{value}</p>
              <p style={{ fontSize: '0.7rem', color: '#4A6285' }}>{sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── DATA SOURCES ── */}
      <section className="glass" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(255, 179, 64, 0.1)', border: '1px solid rgba(255, 179, 64, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Globe size={20} color="#FFB340" />
          </div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: '#EDF4FF' }}>Data Sources</h2>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[
            { label: 'CBSL Daily Market Reports', desc: 'Central Bank of Sri Lanka publishes wholesale fish price data daily. Our scraper ingests this at 5 AM LKT.' },
            { label: '9+ Years Historical Data', desc: 'Training dataset spans from 2015 to present, giving the model exposure to seasonal patterns, inflation cycles, and market shocks.' },
            { label: 'Automated Pipeline', desc: 'GitHub Actions workflow runs daily scraping → feature engineering → model inference → API update with zero manual intervention.' },
          ].map(({ label, desc }) => (
            <div key={label} style={{ display: 'flex', gap: '1rem', padding: '1rem', borderRadius: '0.75rem', background: 'rgba(100, 180, 255, 0.04)', border: '1px solid rgba(100, 180, 255, 0.08)' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#FFB340', marginTop: '6px', flexShrink: 0 }} />
              <div>
                <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#EDF4FF', marginBottom: '0.25rem' }}>{label}</p>
                <p style={{ fontSize: '0.8rem', color: '#4A6285', lineHeight: 1.7, margin: 0 }}>{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── DISCLAIMER & CONTACT ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        <section className="glass" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '1rem' }}>
            <Shield size={18} color="#FF4F6A" />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: '#EDF4FF' }}>Disclaimer</h2>
          </div>
          <p style={{ color: '#4A6285', fontSize: '0.82rem', lineHeight: 1.8, margin: 0 }}>
            Forecasts are AI-generated estimates based on historical patterns and may not reflect sudden market events. 
            This platform is for informational purposes only and should not be the sole basis for financial or procurement decisions.
          </p>
        </section>

        <section className="glass" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '1rem' }}>
            <Mail size={18} color="#00D4FF" />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: '#EDF4FF' }}>Contact</h2>
          </div>
          <p style={{ color: '#4A6285', fontSize: '0.82rem', lineHeight: 1.8, marginBottom: '1rem' }}>
            Have questions, feedback, or want to collaborate? We'd love to hear from you.
          </p>
          <a 
            href="mailto:contact@fishprice.lk" 
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.85rem', fontWeight: 600, color: '#00D4FF', textDecoration: 'none' }}
          >
            <Mail size={14} /> contact@fishprice.lk
          </a>
        </section>
      </div>
    </div>
  );
}
