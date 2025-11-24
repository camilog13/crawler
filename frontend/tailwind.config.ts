import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        seoBg: "#0b1020",
        seoCard: "#141b2f",
        seoAccent: "#3b82f6",
        seoAccentSoft: "#1e293b",
        seoCritical: "#ef4444",
        seoMajor: "#f97316",
        seoMinor: "#eab308"
      }
    }
  },
  plugins: []
};

export default config;
