/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neon: {
          DEFAULT: '#00ff88',
          glow: 'rgba(0, 255, 136, 0.3)',
          dim: 'rgba(0, 255, 136, 0.1)',
        },
        dark: {
          bg: '#000000',
          panel: 'rgba(255, 255, 255, 0.01)',
          border: 'rgba(255, 255, 255, 0.05)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 255, 136, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 255, 136, 0.6), 0 0 10px rgba(0, 255, 136, 0.4)' },
        }
      }
    },
  },
  plugins: [],
}
