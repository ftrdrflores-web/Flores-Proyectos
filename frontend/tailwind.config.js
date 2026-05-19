/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        clan: {
          gold:    '#F5A623',
          gold_dark: '#C47D0E',
          red:     '#E8353A',
          red_dark:'#B01F23',
          dark:    '#0D0F14',
          darker:  '#080A0D',
          surface: '#12151C',
          border:  '#1E2330',
        },
      },
      fontFamily: {
        sans: ['Sora', 'ui-sans-serif', 'system-ui'],
        mono: ['JetBrains Mono', 'ui-monospace'],
      },
      backdropBlur: {
        xs: '2px',
      },
      backgroundImage: {
        'glass-light': 'linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.04) 100%)',
        'glass-dark':  'linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.01) 100%)',
      },
      boxShadow: {
        glass: '0 4px 24px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.1)',
        'glass-sm': '0 2px 12px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.08)',
        'clan-gold': '0 0 20px rgba(245,166,35,0.25)',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.16,1,0.3,1)',
        'pulse-gold': 'pulseGold 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGold: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(245,166,35,0.2)' },
          '50%':       { boxShadow: '0 0 30px rgba(245,166,35,0.5)' },
        },
      },
    },
  },
  plugins: [],
}