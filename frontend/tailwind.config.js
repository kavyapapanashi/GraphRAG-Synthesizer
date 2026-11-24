/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#F4F1EA",
        teal: "#00A896",
        terracotta: "#C94A4A",
        ochre: "#F4D35E",
      },
      fontFamily: {
        heading: ["'Space Grotesk'", "sans-serif"],
        sans: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        'neo': '4px 4px 0px 0px #000000',
        'neo-sm': '2px 2px 0px 0px #000000',
        'neo-lg': '6px 6px 0px 0px #000000',
        'neo-teal': '4px 4px 0px 0px #00A896',
        'neo-terracotta': '4px 4px 0px 0px #C94A4A',
      }
    },
  },
  plugins: [],
}
