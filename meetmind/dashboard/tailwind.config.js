/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: { 50: '#f0f0ff', 100: '#e0e0ff', 200: '#c4b5fd', 300: '#a78bfa', 400: '#8b5cf6', 500: '#7c3aed', 600: '#6d28d9', 700: '#5b21b6', 800: '#4c1d95', 900: '#3b0764' },
        accent: { 400: '#f472b6', 500: '#ec4899', 600: '#db2777' },
      },
    },
  },
  plugins: [],
}
