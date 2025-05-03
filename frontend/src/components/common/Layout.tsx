import React, { ReactNode } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { ProgressIndicator } from './ProgressIndicator';
import { useApplicationState } from '../../contexts/ApplicationContext';

interface LayoutProps {
  children: ReactNode;
  showProgress?: boolean;
}

/**
 * Layout component that provides consistent structure across all pages
 * Includes header, footer, and optional progress indicator
 * Uses semantic HTML for better accessibility
 */
export const Layout: React.FC<LayoutProps> = ({ 
  children, 
  showProgress = true 
}) => {
  const { currentStep } = useApplicationState();

  // Only show progress indicator for workflow steps
  const shouldShowProgress = showProgress && 
    ['upload', 'customize', 'results'].includes(currentStep);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      
      {shouldShowProgress && <ProgressIndicator />}
      
      <main 
        className="flex-grow"
        role="main"
        id="main-content"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>
      
      <Footer />
    </div>
  );
};
