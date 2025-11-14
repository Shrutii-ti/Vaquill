/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'judge-gold': '#D4AF37',
        'justice-blue': '#1E3A8A',
        'side-a-blue': '#3B82F6',
        'side-b-red': '#EF4444',
      },
    },
  },
  plugins: [],
}

