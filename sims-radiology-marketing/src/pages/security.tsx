import React from 'react';
import { SecuritySection } from '../components/SecuritySection';

interface SecurityPageProps {
  onNavigate?: (tab: string) => void;
}

export const SecurityPage: React.FC<SecurityPageProps> = ({ onNavigate }) => {
  return (
    <div className="py-6 space-y-12">
      <SecuritySection
        onRequestWhitepaper={() => onNavigate?.('request-demo')}
        onScheduleDemo={() => onNavigate?.('request-demo')}
      />
    </div>
  );
};

export default SecurityPage;
