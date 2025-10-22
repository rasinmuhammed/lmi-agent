/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',         // ✅ App Router pages and layouts
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',  // ✅ Reusable UI components
    './src/lib/**/*.{js,ts,jsx,tsx,mdx}',         // ✅ Utility or API helper files (if you use Tailwind classes in them)
  ],
  theme: {
    extend: {
      colors: {
        primary: {
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
      },
      animation: {
        fadeIn: 'fadeIn 0.5s ease-out',
        slideUp: 'slideUp 0.4s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
