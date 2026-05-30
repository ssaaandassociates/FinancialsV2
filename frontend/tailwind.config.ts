import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: "#1F2A44", light: "#2D3D5C", pale: "#EEF1F6" },
        gold: { DEFAULT: "#B68B3C", light: "#F4EAD1" },
        ink: "#1F2937",
        muted: "#6B7280",
        line: "#E6E8EE",
        surface: "#F8F9FB",
        ok: "#15803D",
        okpale: "#DCFCE7",
        danger: "#B91C1C",
        dangerpale: "#FEE2E2",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};
export default config;
