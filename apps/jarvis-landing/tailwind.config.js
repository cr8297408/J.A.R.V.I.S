/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        /* ── Apple Design System tokens (CSS var bridge) ── */
        "background-primary":   "var(--color-bg-primary)",
        "background-secondary": "var(--color-bg-secondary)",
        "background-tertiary":  "var(--color-bg-tertiary)",
        "surface-primary":   "var(--color-surface-primary)",
        "surface-secondary": "var(--color-surface-secondary)",
        "surface-glass":     "var(--color-surface-glass)",
        "text-primary":   "var(--color-text-primary)",
        "text-secondary": "var(--color-text-secondary)",
        "text-tertiary":  "var(--color-text-tertiary)",
        "text-inverse":   "var(--color-text-inverse)",
        "border-primary":   "var(--color-border-primary)",
        "border-secondary": "var(--color-border-secondary)",
        "accent-blue":        "var(--color-accent-blue)",
        "accent-blue-hover":  "var(--color-accent-blue-hover)",
        "accent-blue-active": "var(--color-accent-blue-active)",
        "accent-blue-tint":   "var(--color-accent-blue-tint)",
        "status-success": "var(--color-status-success)",
        "status-warning": "var(--color-status-warning)",
        "status-error":   "var(--color-status-error)",
        "status-info":    "var(--color-status-info)",

        /* ── shadcn/ui tokens (preserved for legacy compatibility) ── */
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      boxShadow: {
        xs: "var(--shadow-xs)",
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        xl: "var(--shadow-xl)",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'Cascadia Code', 'monospace'],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "pulse-epic": {
          "0%": { transform: "scale(1)", boxShadow: "0 0 0 0 rgba(0,122,255, 0.7)" },
          "70%": { transform: "scale(1.05)", boxShadow: "0 0 0 15px rgba(0,122,255, 0)" },
          "100%": { transform: "scale(1)", boxShadow: "0 0 0 0 rgba(0,122,255, 0)" },
        },
        "fade-in":  { from: { opacity: "0" }, to: { opacity: "1" } },
        "scale-in": { from: { opacity: "0", transform: "scale(0.96)" }, to: { opacity: "1", transform: "scale(1)" } },
        "slide-up": { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "translateY(0)" } },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "pulse-epic": "pulse-epic 2s infinite",
        "fade-in":  "fade-in 220ms cubic-bezier(0.16,1,0.3,1)",
        "scale-in": "scale-in 220ms cubic-bezier(0.16,1,0.3,1)",
        "slide-up": "slide-up 220ms cubic-bezier(0.16,1,0.3,1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
