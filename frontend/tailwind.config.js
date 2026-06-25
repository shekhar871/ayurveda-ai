/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        saffron: { DEFAULT: "#E8913A", dark: "#C46F1E", light: "#F5B86A" },
        leaf: { DEFAULT: "#2D6A4F", dark: "#1B4332", light: "#52B788" },
        cream: { DEFAULT: "#FBF7F0", dark: "#F0E6D6" },
        bark: { DEFAULT: "#3D2C1E", muted: "#6B5344" },
      },
      fontFamily: {
        display: ["Georgia", "Cambria", "serif"],
        sans: ["system-ui", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
