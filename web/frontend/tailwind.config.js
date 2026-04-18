/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gsh: {
          bg:             '#FFFFFF',
          card:           '#F9F9FB',
          border:         '#E5E7EB',
          accent:         '#8A4DFF',
          'accent-hover': '#7A3DEF',
          muted:          '#6B7280',
          text:           '#0B0F2A',
          cyan:           '#2EC7FF',
          lavender:       '#BFA4FF',
          'code-bg':      '#f6f8fa',
        },
      },
    },
  },
  plugins: [],
}
