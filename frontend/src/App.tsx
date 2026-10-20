import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { HomePage } from './pages/HomePage';
import { DrinksPage } from './pages/DrinksPage';
import { LabPage } from './pages/LabPage';
import { ResultPage } from './pages/ResultPage';
import { HistoryPage } from './pages/HistoryPage';
import { SearchPage } from './pages/SearchPage';
import { AccountPage } from './pages/AccountPage';
import { SettingsPage } from './pages/SettingsPage';
import { AboutPage } from './pages/AboutPage';
import { getSettings, saveSettings, applyTheme } from './services/settingsService';

const AppLayout: React.FC = () => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(() => {
    return typeof window !== 'undefined' ? window.innerWidth >= 1024 : true;
  });

  const [settings, setSettings] = useState(getSettings());

  // Apply saved theme on initial render
  useEffect(() => {
    applyTheme(settings.theme);
  }, [settings.theme]);

  // Handle responsive resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setSidebarOpen(true);
      } else {
        setSidebarOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Auto-close drawer on mobile route changes
  useEffect(() => {
    if (window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const toggleTheme = () => {
    const nextTheme = settings.theme === 'dark' ? 'light' : 'dark';
    const updated = { ...settings, theme: nextTheme as 'light' | 'dark' };
    setSettings(updated);
    saveSettings(updated);
    applyTheme(nextTheme);
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Layout Container */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          marginLeft: typeof window !== 'undefined' && window.innerWidth >= 1024 && sidebarOpen ? 'var(--sidebar-width)' : 0,
          transition: 'margin-left var(--transition-normal)',
          minWidth: 0,
        }}
        className="main-container"
      >
        {/* Global Navigation Header */}
        <Navbar
          onToggleSidebar={toggleSidebar}
          theme={settings.theme}
          onToggleTheme={toggleTheme}
        />

        {/* Routed Page Content */}
        <main
          style={{
            flex: 1,
            padding: 'var(--space-xl) var(--space-lg)',
            width: '100%',
            maxWidth: 'var(--max-content-width)',
            margin: '0 auto',
            boxSizing: 'border-box',
          }}
        >
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/drinks" element={<Navigate to="/drinks/soft-drinks" replace />} />
            <Route path="/drinks/:category" element={<DrinksPage />} />
            <Route path="/lab" element={<LabPage />} />
            <Route path="/result" element={<ResultPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/account" element={<AccountPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
};

export default App;
