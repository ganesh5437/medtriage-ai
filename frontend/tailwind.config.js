/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0f172a",
        surface: "#1e293b",
        teal: { DEFAULT: "#0d9488", light: "#2dd4bf" },
        textdim: "#94a3b8",
        border: "#334155",
        emred: "#dc2626",
        amber: "#d97706",
        green: "#16a34a",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
