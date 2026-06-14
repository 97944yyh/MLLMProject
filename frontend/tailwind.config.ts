import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#192231",
        mist: "#f6f8fb",
        line: "#dde7ef",
        aqua: "#49b9c7",
        iris: "#6476f2",
        leaf: "#65b687",
        amberSoft: "#fff1d6"
      },
      boxShadow: {
        soft: "0 18px 60px rgba(36, 48, 64, 0.12)",
        lift: "0 18px 40px rgba(75, 92, 112, 0.18)"
      }
    }
  },
  plugins: []
} satisfies Config;
