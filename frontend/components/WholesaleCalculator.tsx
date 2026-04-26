'use client';

import { useState } from 'react';
import { Calculator, ShoppingCart, TrendingDown } from 'lucide-react';
import type { ForecastPoint } from '@/types';

type Props = {
  forecast: ForecastPoint[];
};

export default function WholesaleCalculator({ forecast }: Props) {
  const [quantity, setQuantity] = useState<number>(50);
  
  if (!forecast || forecast.length === 0) return null;

  const bestDay = [...forecast].sort((a, b) => a.prediction - b.prediction)[0];

  return (
    <div className="glass" style={{ padding: '1.5rem', marginTop: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <div style={{
          width: '40px', height: '40px',
          borderRadius: '10px',
          background: 'rgba(0, 212, 255, 0.1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#00D4FF'
        }}>
          <Calculator size={20} />
        </div>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#EDF4FF' }}>Wholesale Volume Calculator</h3>
          <p style={{ fontSize: '0.8rem', color: '#4A6285' }}>Estimate total cost based on the 3-day forecast</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', alignItems: 'end' }}>
        {/* Input */}
        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#4A6285', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
            Quantity (kg)
          </label>
          <div style={{ position: 'relative' }}>
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              style={{
                width: '100%',
                background: 'rgba(13, 21, 38, 0.6)',
                border: '1px solid rgba(100, 180, 255, 0.15)',
                borderRadius: '0.75rem',
                padding: '0.75rem 1rem',
                color: '#EDF4FF',
                fontSize: '1.1rem',
                fontWeight: 600,
                outline: 'none',
              }}
            />
            <div style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#4A6285', fontSize: '0.8rem', fontWeight: 600 }}>
              KG
            </div>
          </div>
        </div>

        {/* Best Buy Suggestion */}
        <div style={{
          background: 'rgba(16, 217, 160, 0.05)',
          border: '1px solid rgba(16, 217, 160, 0.15)',
          borderRadius: '0.75rem',
          padding: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div style={{ color: '#10D9A0' }}><TrendingDown size={24} /></div>
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#10D9A0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Best Day to Buy</div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#EDF4FF' }}>{bestDay.dateLabel}</div>
            <div style={{ fontSize: '0.8rem', color: '#7A9CC9' }}>Est. Total: Rs. {(bestDay.prediction * quantity).toLocaleString()}</div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
        {forecast.map(day => (
          <div key={day.dateLabel} style={{
            background: day.dateLabel === bestDay.dateLabel ? 'rgba(0, 212, 255, 0.05)' : 'rgba(255, 255, 255, 0.02)',
            border: `1px solid ${day.dateLabel === bestDay.dateLabel ? 'rgba(0, 212, 255, 0.2)' : 'rgba(100, 180, 255, 0.08)'}`,
            borderRadius: '0.75rem',
            padding: '1rem',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.7rem', color: '#4A6285', marginBottom: '0.25rem' }}>{day.dateLabel}</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: day.dateLabel === bestDay.dateLabel ? '#00D4FF' : '#EDF4FF' }}>
              Rs. {(day.prediction * quantity).toLocaleString()}
            </div>
            <div style={{ fontSize: '0.65rem', color: '#7A9CC9', marginTop: '0.25rem' }}>Rs. {day.prediction}/kg</div>
          </div>
        ))}
      </div>
    </div>
  );
}
