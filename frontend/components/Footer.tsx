'use client';

import Link from 'next/link';
import { Activity, Github, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer style={{
      marginTop: '5rem',
      borderTop: '1px solid rgba(100, 180, 255, 0.08)',
      background: 'rgba(7, 11, 20, 0.7)',
      backdropFilter: 'blur(20px)',
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '3rem 1.5rem 2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem', marginBottom: '2.5rem' }}>
          
          {/* Brand */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.875rem' }}>
              <div style={{
                width: '34px', height: '34px',
                borderRadius: '9px',
                background: 'linear-gradient(135deg, #00B4A0, #00D4FF)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 0 12px rgba(0, 212, 255, 0.25)',
              }}>
                <Activity size={16} color="#070B14" strokeWidth={2.5} />
              </div>
              <span style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 800, fontSize: '1rem', color: '#EDF4FF' }}>
                FishPrice<span style={{ color: '#00D4FF' }}>.LK</span>
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#4A6285', lineHeight: 1.7, maxWidth: '220px' }}>
              AI-powered price predictions for the Peliyagoda fish market using real-time data.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#4A6285', marginBottom: '1rem', fontFamily: 'inherit' }}>
              Navigation
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              {[
                { href: '/', label: 'Home' },
                { href: '/forecast', label: 'Forecast' },
                { href: '/history', label: 'Historical Data' },
                { href: '/about', label: 'About' },
              ].map(item => (
                <Link key={item.href} href={item.href} className="footer-link">
                  {item.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Data */}
          <div>
            <h4 style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#4A6285', marginBottom: '1rem', fontFamily: 'inherit' }}>
              Data Sources
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              {['CBSL Market Reports', 'Open-Meteo Weather', 'Ceypetco Fuel Prices', 'Historical Records'].map(s => (
                <span key={s} style={{ fontSize: '0.825rem', color: '#4A6285' }}>{s}</span>
              ))}
            </div>
          </div>

          {/* Disclaimer */}
          <div>
            <h4 style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#4A6285', marginBottom: '1rem', fontFamily: 'inherit' }}>
              Disclaimer
            </h4>
            <p style={{ fontSize: '0.8rem', color: '#4A6285', lineHeight: 1.7 }}>
              Price forecasts are AI-generated estimates. Do not use as the sole basis for financial decisions.
            </p>
          </div>
        </div>

        {/* Bottom bar */}
        <div style={{
          paddingTop: '1.5rem',
          borderTop: '1px solid rgba(100, 180, 255, 0.06)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}>
          <p style={{ fontSize: '0.75rem', color: '#4A6285' }}>
            © {new Date().getFullYear()} FishPrice.LK — Made for Sri Lankan fish markets
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', color: '#4A6285' }}>
            <span>Built with</span>
            <Heart size={12} color="#FF4F6A" fill="#FF4F6A" />
            <span>and XGBoost</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
