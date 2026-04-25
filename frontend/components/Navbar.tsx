'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const navItems = [
  { href: '/forecast', label: 'Forecast' },
  { href: '/history', label: 'Historical Data' },
  { href: '/about', label: 'About' }
];

export default function Navbar() {
  const [isShrunk, setIsShrunk] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setIsShrunk(window.scrollY > 10);
    onScroll();
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={[
        'sticky top-0 z-50 w-full border-b border-black/5 backdrop-blur',
        'bg-brand-background/80',
        isShrunk ? 'py-2' : 'py-3'
      ].join(' ')}
    >
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-lg bg-brand-primary text-white grid place-items-center font-bold text-sm">
            FP
          </div>
          <div className="leading-tight">
            <div className="font-semibold text-brand-primary">FishPrice.LK</div>
            <div className="text-xs text-brand-neutral">Peliyagoda market</div>
          </div>
        </Link>

        <nav className="hidden items-center gap-2 md:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-lg px-3 py-2 text-sm font-medium text-brand-neutral transition hover:bg-brand-light hover:text-brand-primary"
            >
              {item.label}
            </Link>
          ))}
          <Link
            href="/forecast"
            className="ml-2 rounded-lg bg-brand-primary px-4 py-2 text-sm text-white shadow-sm transition hover:bg-brand-secondary"
          >
            View details
          </Link>
        </nav>

        <button
          className="md:hidden rounded-lg p-2 hover:bg-brand-light"
          aria-label="Open menu"
          onClick={() => setMobileOpen((v) => !v)}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="md:hidden overflow-hidden border-t border-black/5 bg-white"
          >
            <div className="mx-auto w-full max-w-6xl px-4 py-3 flex flex-col gap-2">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className="rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-brand-light"
                >
                  {item.label}
                </Link>
              ))}
              <Link
                href="/forecast"
                onClick={() => setMobileOpen(false)}
                className="rounded-lg bg-brand-primary px-3 py-2 text-sm text-white"
              >
                View detailed forecast
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
