import React from 'react';
import { Header } from './Header';
import { Footer } from './Footer';

interface BaseLayoutProps {
  children: React.ReactNode;
  activePage: string;
  onNavigate: (page: string) => void;
}

export const BaseLayout: React.FC<BaseLayoutProps> = ({ children, activePage, onNavigate }) => {
  return (
    <div className="flex flex-col min-h-screen bg-clinical-950 text-slate-100">
      <Header activePage={activePage} onNavigate={onNavigate} />
      <main className="flex-grow">
        {children}
      </main>
      <Footer onNavigate={onNavigate} />
    </div>
  );
};
