/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f3f9f0',
          100: '#e4f2dc',
          200: '#c6e4ba',
          300: '#9dcf8e',
          400: '#6fb560',
          500: '#4d9a3e',  // primary green
          600: '#3b7c2f',
          700: '#306327',
          800: '#294f22',
          900: '#23421e',
        },
        warm: {
          50:  '#fdf8f0',
          100: '#faefd9',
          200: '#f4dcad',
          300: '#edc278',
          400: '#e5a245',
          500: '#df8820',  // warm amber accent
          600: '#c46f15',
          700: '#a35514',
          800: '#844418',
          900: '#6c3917',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
