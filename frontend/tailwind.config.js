/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        xiaomi: {
          orange: '#FF6900',
          dark: '#1a1a2e',
          darker: '#16213e',
          card: '#1e293b',
        },
      },
    },
  },
  plugins: [],
}
