import React from 'react';

/**
 * Footer component with copyright and links
 * Includes accessibility features and semantic HTML
 */
export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-50 border-t border-gray-200" role="contentinfo">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="md:flex md:items-center md:justify-between">
          {/* Copyright section */}
          <div className="text-center md:text-left">
            <p className="text-sm text-gray-500">
              © {currentYear} ResumeAI. All rights reserved.
            </p>
          </div>
          
          {/* Links section */}
          <nav 
            className="mt-4 md:mt-0"
            aria-label="Footer navigation"
          >
            <ul className="flex justify-center md:justify-end space-x-6">
              <li>
                <a 
                  href="#privacy" 
                  className="text-sm text-gray-500 hover:text-gray-900"
                >
                  Privacy Policy
                </a>
              </li>
              <li>
                <a 
                  href="#terms" 
                  className="text-sm text-gray-500 hover:text-gray-900"
                >
                  Terms of Service
                </a>
              </li>
              <li>
                <a 
                  href="#contact" 
                  className="text-sm text-gray-500 hover:text-gray-900"
                >
                  Contact Us
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </footer>
  );
};
