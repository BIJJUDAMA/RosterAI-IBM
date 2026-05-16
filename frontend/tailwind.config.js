/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#252220",
        paper: "#f4f0e8",
        mist: "#dfd6c8",
        moss: "#5c6a57",
        clay: "#9b7b56",
        line: "#c7b9a4",
      },
      fontFamily: {
        display: ['Cormorant Garamond', 'serif'],
        body: ['IBM Plex Sans', 'sans-serif'],
      },
      animation: {
        'breath': 'breath 5s ease-in-out infinite',
      },
      keyframes: {
        breath: {
          '0%, 100%': { transform: 'rotate(-20deg) scale(1)', opacity: '0.85' },
          '50%': { transform: 'rotate(-20deg) scale(1.04)', opacity: '1' },
        }
      },
      backgroundImage: {
        'zen-gradient': "radial-gradient(circle at 20% 20%, rgba(155, 123, 86, 0.18), transparent 45%), radial-gradient(circle at 80% 80%, rgba(92, 106, 87, 0.14), transparent 40%)",
      }
    },
  },
  plugins: [],
}
