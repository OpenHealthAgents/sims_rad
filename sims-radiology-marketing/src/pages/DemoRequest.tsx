import React from 'react';
import { RequestDemoPage } from './request-demo';

export const DemoRequest: React.FC<{ onSubmitSuccess?: () => void }> = () => {
  return <RequestDemoPage />;
};

export default DemoRequest;
