import React from 'react';
import { Navigate } from 'react-router-dom';

export default function ProtectedRoute({ children }) {
  // Check if user is authenticated via localStorage token
  // Support both test token and production tokens
  const isAuthenticated = !!localStorage.getItem('authToken') || !!localStorage.getItem('kibray_access_token');

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
