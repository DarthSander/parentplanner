import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#FAF8F5",
        surface: "#FFFFFF",
        "surface-alt": "#F2EDE8",
        primary: "#4A6741",
        "primary-light": "#7A9E72",
        accent: "#C4783A",
        "accent-light": "#E8A96D",
        "text-main": "#2C2C2C",
        "text-muted": "#7A7269",
        danger: "#C0392B",
        warning: "#E67E22",
        success: "#27AE60",
        border: "#E0D9D1",
      },
      borderRadius: {
        sm: "8px",
        md: "14px",
        lg: "22px",
      },
      fontFamily: {
        display: ["Lora", "Georgia", "serif"],
        body: ["DM Sans", "system-ui", "sans-serif"],
      },
      boxShadow: {
        sm: "0 1px 3px rgba(0,0,0,0.06)",
        md: "0 4px 12px rgba(0,0,0,0.08)",
        lg: "0 8px 24px rgba(0,0,0,0.10)",
      },
    },
  },
  plugins: [],
};

export default config;
