/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    container: {
      center: true,
      padding: {
        DEFAULT: '1rem',
        sm: '1.5rem',
        lg: '2rem',
        xl: '2.5rem',
      },
    },
    extend: {
      colors: {
        // Core SIMS Radiology Palette
        navy: {
          950: '#071224',
          900: '#0B1C34', // Primary Dark Navy
          850: '#102646',
          800: '#18355E',
          700: '#22487A',
          600: '#2F619F',
          500: '#437EC4',
          400: '#6C9DE0',
          300: '#9EBFED',
          200: '#CADDF6',
          100: '#E8F1FC',
          50: '#F4F8FD',
        },
        teal: {
          700: '#007575',
          600: '#008B8B',
          500: '#00A6A6', // Secondary Accent Teal
          400: '#1CBABA',
          300: '#46CDCD',
          200: '#83E0E0',
          100: '#C2F2F2',
          50: '#E8FAFA',
        },
        cyan: {
          600: '#1FAABF',
          500: '#2DC4DC', // Highlights Cyan
          400: '#52D1E4',
          300: '#7CE0EE',
          200: '#ABEBF5',
          100: '#D5F5FA',
          50: '#EEFBFD',
        },
        surface: {
          light: '#FAFCFD', // Clean background
          lightCard: '#FFFFFF',
          lightBorder: '#E1E9F2',
          dark: '#071224',
          darkCard: '#0B1C34',
          darkCardElevated: '#102646',
          darkBorder: '#18355E',
        },
        clinical: {
          stat: '#EF4444',     // Critical triage (STAT)
          urgent: '#F59E0B',   // Urgent (< 45m)
          routine: '#3B82F6',  // Routine queue
          verified: '#10B981', // Guardrail Verified Safe
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'teal-cyan-gradient': 'linear-gradient(135deg, #00A6A6 0%, #2DC4DC 100%)',
        'navy-deep-gradient': 'linear-gradient(180deg, #071224 0%, #0B1C34 100%)',
        'mesh-glow': 'radial-gradient(circle at 50% 20%, rgba(45, 196, 220, 0.15) 0%, rgba(0, 166, 166, 0.05) 50%, transparent 80%)',
      },
      boxShadow: {
        'glow-teal': '0 0 25px -4px rgba(0, 166, 166, 0.35)',
        'glow-cyan': '0 0 25px -4px rgba(45, 196, 220, 0.40)',
        'medical-card': '0 10px 30px -5px rgba(11, 28, 52, 0.06), 0 4px 10px -2px rgba(11, 28, 52, 0.03)',
        'medical-card-dark': '0 10px 30px -5px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(24, 53, 94, 0.8)',
      }
    },
  },
  plugins: [],
}
