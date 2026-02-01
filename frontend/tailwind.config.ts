import type { Config } from 'tailwindcss';

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#0A7AFF',
          secondary: '#1E40AF',
          accent: '#38BDF8',
          light: '#DBEAFE',
          success: '#10B981',
          alert: '#EF4444',
          neutral: '#64748B',
          background: '#F8FAFC',
          white: '#FFFFFF'
        }
      }
    }
  },
  plugins: []
} satisfies Config;
