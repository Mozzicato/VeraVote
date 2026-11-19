import type { Config } from "tailwindcss";

const token = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;
const names = [
  "paper", "sheet", "rule", "ink", "ink-soft", "violet", "violet-strong", "on-violet",
  "agree", "agree-tint", "differ", "differ-tint", "wait", "wait-tint", "done", "done-tint", "hatch",
];

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: Object.fromEntries(names.map((n) => [n, token(n)])),
      fontFamily: {
        sans: ["var(--font-atkinson)", "system-ui", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Consolas", "monospace"],
      },
      // Modular scale (1.25) on a 17px base, per Bringhurst's preference for a few clear steps.
      fontSize: {
        xs: ["0.8125rem", { lineHeight: "1.4" }],
        sm: ["0.9375rem", { lineHeight: "1.5" }],
        base: ["1.0625rem", { lineHeight: "1.55" }],
        lg: ["1.3125rem", { lineHeight: "1.35" }],
        xl: ["1.625rem", { lineHeight: "1.2" }],
        "2xl": ["2.0625rem", { lineHeight: "1.1" }],
        "3xl": ["2.5625rem", { lineHeight: "1.05" }],
      },
      maxWidth: { measure: "68ch" },
    },
  },
  plugins: [],
} satisfies Config;
