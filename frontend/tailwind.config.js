/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "Inter", "sans-serif"],
      },
      colors: {
        garage: {
          950: "#070a0f",
          900: "#0c1119",
          850: "#111827",
        },
        accent: {
          DEFAULT: "#f59e0b",
          dim: "#d97706",
        },
      },
      boxShadow: {
        panel: "0 0 0 1px rgba(255,255,255,0.06), 0 18px 50px rgba(0,0,0,0.55)",
      },
    },
  },
  plugins: [],
};
