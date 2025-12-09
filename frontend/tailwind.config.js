/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a', // Deep slate for dark aesthetic
        surface: 'rgba(255, 255, 255, 0.05)',
        surfaceHighlight: 'rgba(255, 255, 255, 0.1)',
        primary: {
          DEFAULT: '#3b82f6',
          glow: 'rgba(59, 130, 246, 0.5)',
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        accent: {
          cyan: '#06b6d4',
          teal: '#14b8a6',
          purple: '#8b5cf6',
        }
      },
      animation: {
        fadeIn: 'fadeIn 0.6s ease-out forwards',
        slideUp: 'slideUp 0.5s ease-out forwards',
        pulseSlow: 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        shimmer: 'shimmer 2.5s infinite linear',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        }
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
};
