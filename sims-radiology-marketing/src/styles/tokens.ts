/**
 * SIMS Radiology AI Operating Platform Design Tokens
 * Master Theme Specification
 */
export const medicalDesignTokens = {
  palette: {
    primaryNavy: '#0B1C34', // Deep Tech Navy
    secondaryTeal: '#00A6A6', // Secondary Clinical Teal
    highlightCyan: '#2DC4DC', // High-Acuity Cyan
    cleanBackground: '#FAFCFD', // Pristine Clinical Light Surface
    deepBackground: '#071224', // Reading Room Dark
  },
  status: {
    stat: '#EF4444',      // Immediate emergent triage (ICH, PE, Tension Pneumo)
    urgent: '#F59E0B',    // Expedited turnaround (< 45m)
    routine: '#3B82F6',   // Standard read list
    verified: '#10B981',  // NVIDIA NeMo Guardrails Verified
  },
  typography: {
    body: 'Inter, system-ui, -apple-system, Arial, sans-serif',
    mono: 'JetBrains Mono, monospace',
  }
};
