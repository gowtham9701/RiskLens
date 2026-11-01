import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#070b17",
          900: "#0b1120",
          850: "#0f1729",
          800: "#131c31",
          700: "#1c2740",
          600: "#263251",
          500: "#36456b",
        },
        accent: {
          DEFAULT: "#3b82f6",
          hover: "#2563eb",
        },
        positive: "#22c55e",
        negative: "#ef4444",
        warning: "#f59e0b",
      },
      fontFamily: {
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui"],
      },
    },
  },
  plugins: [],
};
export default config;
