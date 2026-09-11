/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#F8F7F5',
        ground: '#F8F7F5',
        surface: '#FFFFFF',
        topbar: '#0D0D14',
        accent: '#E8002D',
        'accent-dark': '#C0001F',
        ink: '#18181B',
        muted: '#6B6876',
        border: '#E4E4E8',
        'border-strong': '#D1D1D8',
        positive: '#16a34a',
        negative: '#dc2626',
        warning: '#d97706',
      },
      fontFamily: {
        display: ['Orbitron', 'sans-serif'],
        label: ['Rajdhani', 'sans-serif'],
        data: ['"Barlow Condensed"', 'sans-serif'],
        body: ['Barlow', 'sans-serif'],
      },
      fontSize: {
        'fluid-hero': ['clamp(2.75rem, 1.5rem + 6vw, 5.25rem)', { lineHeight: '0.92', letterSpacing: '-0.03em' }],
        'fluid-lead': ['clamp(1rem, 0.9rem + 0.6vw, 1.2rem)', { lineHeight: '1.55' }],
      },
      transitionTimingFunction: {
        'out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        riseIn: {
          '0%': { opacity: '0', transform: 'translateY(26px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
        pulse_soft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
        spin_smooth: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        fadeUp: 'fadeUp 0.5s ease-out both',
        riseIn: 'riseIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) both',
        shimmer: 'shimmer 1.4s ease-in-out infinite',
        pulse_soft: 'pulse_soft 1.8s ease-in-out infinite',
        spin_smooth: 'spin_smooth 0.8s linear infinite',
      },
    },
  },
  plugins: [],
}
