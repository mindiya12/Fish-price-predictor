'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { Menu, X, TrendingUp, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/forecast', label: 'Forecast' },
  { href: '/history', label: 'Historical Data' },
  { href: '/about', label: 'About' },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    onScroll();
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        transition: 'all 0.3s ease',
        background: scrolled
          ? 'rgba(7, 11, 20, 0.85)'
          : 'transparent',
        backdropFilter: scrolled ? 'blur(20px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(100, 180, 255, 0.08)' : '1px solid transparent',
      }}
    >
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: scrolled ? '60px' : '70px', transition: 'height 0.3s ease' }}>
          
          {/* Logo */}
          <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none' }}>
            <div style={{
              width: '38px', height: '38px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #00B4A0, #00D4FF)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 16px rgba(0, 212, 255, 0.35)',
            }}>
              <Activity size={18} color="#070B14" strokeWidth={2.5} />
            </div>
            <div>
              <div style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 800, fontSize: '1rem', color: '#EDF4FF', letterSpacing: '-0.02em' }}>
                FishPrice<span style={{ color: '#00D4FF' }}>.LK</span>
              </div>
              <div style={{ fontSize: '0.65rem', color: '#4A6285', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                Peliyagoda Market
              </div>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }} className="hidden-mobile">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-link ${isActive ? 'active' : ''}`}
                >
                  {item.label}
                </Link>
              );
            })}
            <Link
              href="/forecast"
              className="btn-primary"
              style={{ marginLeft: '0.5rem', textDecoration: 'none', fontSize: '0.875rem' }}
            >
              View Forecast →
            </Link>
          </nav>

          {/* Mobile toggle */}
          <button
            onClick={() => setMobileOpen(v => !v)}
            style={{
              display: 'none',
              background: 'rgba(0, 212, 255, 0.07)',
              border: '1px solid rgba(0, 212, 255, 0.15)',
              borderRadius: '0.5rem',
              padding: '0.5rem',
              color: '#7A9CC9',
              cursor: 'pointer',
            }}
            className="show-mobile"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{
              overflow: 'hidden',
              borderTop: '1px solid rgba(100, 180, 255, 0.08)',
              background: 'rgba(7, 11, 20, 0.95)',
              backdropFilter: 'blur(20px)',
            }}
          >
            <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  style={{
                    padding: '0.75rem 1rem',
                    borderRadius: '0.5rem',
                    color: '#7A9CC9',
                    textDecoration: 'none',
                    fontSize: '0.9rem',
                    fontWeight: 500,
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(100,180,255,0.06)',
                  }}
                >
                  {item.label}
                </Link>
              ))}
              <Link
                href="/forecast"
                onClick={() => setMobileOpen(false)}
                className="btn-primary"
                style={{ textDecoration: 'none', textAlign: 'center', marginTop: '0.25rem' }}
              >
                View Forecast →
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @media (max-width: 768px) {
          .hidden-mobile { display: none !important; }
          .show-mobile { display: flex !important; }
        }
      `}</style>
    </header>
  );
}
