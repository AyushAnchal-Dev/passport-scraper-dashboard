/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'hsl(224, 71%, 4%)',
        foreground: 'hsl(213, 31%, 91%)',
        card: 'rgba(10, 15, 30, 0.7)',
        border: 'rgba(255, 255, 255, 0.08)',
        accent: {
          purple: '#8b5cf6',
          cyan: '#06b6d4',
          pink: '#ec4899',
          green: '#10b981',
          yellow: '#f59e0b',
        },
        muted: 'hsl(215, 20.2%, 65.1%)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        'glow-purple': '0 0 15px rgba(139, 92, 246, 0.4)',
        'glow-cyan': '0 0 15px rgba(6, 182, 212, 0.4)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      animation: {
        'border-pulse': 'borderPulse 4s infinite alternate',
      },
      keyframes: {
        borderPulse: {
          '0%': { borderColor: 'rgba(139, 92, 246, 0.2)' },
          '50%': { borderColor: 'rgba(6, 182, 212, 0.5)' },
          '100%': { borderColor: 'rgba(236, 72, 153, 0.2)' },
        }
      }
    },
  },
  plugins: [],
}
