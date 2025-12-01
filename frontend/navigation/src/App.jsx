import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { NavigationProvider } from './context/NavigationContext.jsx';
import { RoleProvider } from './context/RoleContext.jsx';
import { ThemeProvider } from './context/ThemeContext.jsx';
import './styles/global.css';

// Auth components
import Login from './components/auth/Login.jsx';
import ProtectedRoute from './components/auth/ProtectedRoute.jsx';

// Phase 4 feature components
import FileManager from './components/files/FileManager.jsx';
import UserManagement from './components/users/UserManagement.jsx';
import CalendarView from './components/calendar/CalendarView.jsx';
import ChatPanel from './components/chat/ChatPanel.jsx';
import NotificationCenter from './components/notifications/NotificationCenter.jsx';
import GlobalSearch from './components/search/GlobalSearch.jsx';
import ReportGenerator from './components/reports/ReportGenerator.jsx';

// Pages
import Dashboard from './pages/Dashboard.jsx';

// Layout wrapper for protected routes
function MainLayout({ children }) {
  return (
    <div className="app-container">
      <NotificationCenter />
      <main className="main-content">
        {children}
      </main>
      <GlobalSearch />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <RoleProvider>
          <NavigationProvider>
            <Routes>
              {/* Public route */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <MainLayout>
                    <Navigate to="/dashboard" replace />
                  </MainLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <MainLayout>
                    <Dashboard />
                  </MainLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/files" element={
                <ProtectedRoute>
                  <MainLayout>
                    <FileManager />
                  </MainLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/users" element={
                <ProtectedRoute>
                  <MainLayout>
                    <UserManagement />
                  </MainLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/calendar" element={
                <ProtectedRoute>
                  <MainLayout>
                    <CalendarView />
                  </MainLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/chat" element={
                <ProtectedRoute>
                  <MainLayout>
                    <ChatPanel />
                  </MainLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/reports" element={
                <ProtectedRoute>
                  <MainLayout>
                    <ReportGenerator />
                  </MainLayout>
                </ProtectedRoute>
              } />
              
              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </NavigationProvider>
        </RoleProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
export { App };
