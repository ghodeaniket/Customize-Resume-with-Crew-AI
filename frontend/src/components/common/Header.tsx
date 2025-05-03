import React from 'react';

/**
 * Header component displays the application logo and navigation
 * Following accessibility best practices with semantic HTML
 */
export const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm" role="banner">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo section */}
          <div className="flex items-center">
            <a 
              href="/" 
              className="text-2xl font-bold text-blue-600"
              aria-label="ResumeAI - Home"
            >
              ResumeAI
            </a>
          </div>
          
          {/* Navigation section */}
          <nav aria-label="Main navigation">
            <div className="flex items-center space-x-4">
              <a 
                href="#how-it-works" 
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                How It Works
              </a>
              <a 
                href="#pricing" 
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Pricing
              </a>
              <button 
                className="bg-blue-100 text-blue-700 hover:bg-blue-200 px-4 py-2 rounded-full text-sm font-semibold transition-colors"
                aria-label="Sign In"
              >
                Sign In
              </button>
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};
