import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ApplicationProvider } from './contexts/ApplicationContext';
import { Layout } from './components/common/Layout';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { UploadPage } from './pages/UploadPage';
import { CustomizePage } from './pages/CustomizePage';
import { ResultsPage } from './pages/ResultsPage';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { GlobalErrorHandler } from './components/common/GlobalErrorHandler';

/**
 * Main App component with routing and global state management
 * Implements the workflow: upload → customize → results
 * Includes error boundary for catching React errors
 */
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <ApplicationProvider>
        <Router>
          <GlobalErrorHandler />
          <Layout>
            <Routes>
              {/* Main workflow routes */}
              <Route 
                path="/" 
                element={
                  <ProtectedRoute requiredStep="upload">
                    <UploadPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/customize" 
                element={
                  <ProtectedRoute requiredStep="customize">
                    <CustomizePage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/results" 
                element={
                  <ProtectedRoute requiredStep="results">
                    <ResultsPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        </Router>
      </ApplicationProvider>
    </ErrorBoundary>
  );
};

export default App;
