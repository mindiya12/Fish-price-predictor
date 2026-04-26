'use client';

import { useState } from 'react';
import { Bell, CheckCircle2, Loader2 } from 'lucide-react';

export default function PriceAlertForm() {
  const [email, setEmail] = useState('');
  const [targetPrice, setTargetPrice] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/alerts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          target_price: parseFloat(targetPrice),
          fish: 'balaya',
          location: 'peliyagoda'
        })
      });

      if (response.ok) {
        setStatus('success');
        setEmail('');
        setTargetPrice('');
        setTimeout(() => setStatus('idle'), 5000);
      } else {
        setStatus('error');
      }
    } catch (err) {
      setStatus('error');
    }
  };

  return (
    <div className="glass" style={{ padding: '1.5rem', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
        <div style={{
          width: '36px', height: '36px',
          borderRadius: '9px',
          background: 'rgba(255, 193, 7, 0.1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#FFC107'
        }}>
          <Bell size={18} />
        </div>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#EDF4FF' }}>Price Threshold Alerts</h3>
      </div>

      <p style={{ fontSize: '0.8rem', color: '#7A9CC9', marginBottom: '1.25rem', lineHeight: 1.5 }}>
        Get notified via email when the predicted price drops below your target.
      </p>

      {status === 'success' ? (
        <div style={{
          background: 'rgba(16, 217, 160, 0.1)',
          border: '1px solid rgba(16, 217, 160, 0.2)',
          borderRadius: '0.75rem',
          padding: '1.5rem',
          textAlign: 'center',
          color: '#10D9A0'
        }}>
          <CheckCircle2 size={32} style={{ margin: '0 auto 0.75rem' }} />
          <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Alert Set Successfully!</div>
          <div style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>We&apos;ll email you when the price hits your target.</div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#4A6285', marginBottom: '0.375rem', textTransform: 'uppercase' }}>
              Target Price (Rs./kg)
            </label>
            <input
              type="number"
              placeholder="e.g. 900"
              required
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(13, 21, 38, 0.6)',
                border: '1px solid rgba(100, 180, 255, 0.15)',
                borderRadius: '0.625rem',
                padding: '0.625rem 0.875rem',
                color: '#EDF4FF',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#4A6285', marginBottom: '0.375rem', textTransform: 'uppercase' }}>
              Email Address
            </label>
            <input
              type="email"
              placeholder="you@example.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(13, 21, 38, 0.6)',
                border: '1px solid rgba(100, 180, 255, 0.15)',
                borderRadius: '0.625rem',
                padding: '0.625rem 0.875rem',
                color: '#EDF4FF',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={status === 'loading'}
            className="btn-primary"
            style={{
              marginTop: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              padding: '0.75rem'
            }}
          >
            {status === 'loading' ? <Loader2 size={18} className="animate-spin" /> : <Bell size={16} />}
            Set Alert
          </button>
          
          {status === 'error' && (
            <p style={{ fontSize: '0.75rem', color: '#FF4F6A', textAlign: 'center' }}>
              Something went wrong. Please try again.
            </p>
          )}
        </form>
      )}
    </div>
  );
}
