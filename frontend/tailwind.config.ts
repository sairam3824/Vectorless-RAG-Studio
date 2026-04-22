import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      boxShadow: {
        panel: "0 24px 70px -32px rgba(15, 23, 42, 0.3)",
      },
      colors: {
        ink: "#111827",
        mist: "#f5f7fb",
        accent: {
          50: "#effcf7",
          100: "#d7f7e8",
          500: "#1f8f63",
          600: "#16714f",
        },
        ocean: {
          100: "#dff3ff",
          500: "#1675c1",
          700: "#0c4a77",
        },
      },
      backgroundImage: {
        "grid-fade":
          "radial-gradient(circle at top right, rgba(22,117,193,0.15), transparent 30%), radial-gradient(circle at left bottom, rgba(31,143,99,0.14), transparent 28%)",
      },
    },
  },
  plugins: [],
};

export default config;
