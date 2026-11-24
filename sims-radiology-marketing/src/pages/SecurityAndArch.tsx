import React from 'react';
import { SecuritySection } from '../components/SecuritySection';

export const SecurityAndArch: React.FC<{ onNavigate: (page: string) => void }> = ({ onNavigate }) => {
  return (
    <div className="py-6 space-y-12">
      <SecuritySection
        onRequestWhitepaper={() => onNavigate('request-demo')}
        onScheduleDemo={() => onNavigate('request-demo')}
      />
    </div>
  );
};

export default SecurityAndArch;
