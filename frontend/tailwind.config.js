/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0B0C0F",
        panel: "#151821",
        panel2: "#1B1F2A",
        border: "#272B36",
        amber: {
          DEFAULT: "#E8B454",
          dim: "#C99A3E",
          glow: "#F5C978",
        },
        ink: "#F5F1E8",
        muted: "#8B8D93",
        danger: "#E8544A",
        success: "#5FAE72",
        warn: "#E8B454",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Manrope", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      boxShadow: {
        glow: "0 0 40px -10px rgba(232, 180, 84, 0.35)",
      },
    },
  },
  plugins: [],
};
