import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  Wine,
  Beer,
  Zap,
  Coffee,
  Flame,
  ChevronDown,
  ChevronRight,
  FlaskConical,
  History,
  Info,
  Search,
  User,
  Settings,
  X,
  Layers,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const [drinksOpen, setDrinksOpen] = useState(
    location.pathname.startsWith('/drinks')
  );

  // Auto-expand drinks dropdown if currently viewing a drinks category
  useEffect(() => {
    if (location.pathname.startsWith('/drinks')) {
      setDrinksOpen(true);
    }
  }, [location.pathname]);

  // Lock body scroll on mobile drawer open
  useEffect(() => {
    if (isOpen && window.innerWidth < 1024) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const drinksSubmenu = [
    { name: 'Soft Drinks', path: '/drinks/soft-drinks', icon: Coffee },
    { name: 'Beer', path: '/drinks/beer', icon: Beer },
    { name: 'Energy Drinks', path: '/drinks/energy-drinks', icon: Zap },
    { name: 'Wine', path: '/drinks/wine', icon: Wine },
    { name: 'Alcohol / Spirits', path: '/drinks/alcohol', icon: Flame },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <>
      {/* Mobile Backdrop Scrim */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(11, 31, 58, 0.4)',
            backdropFilter: 'blur(4px)',
            zIndex: 45,
          }}
          className="lg-hidden"
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          bottom: 0,
          width: 'var(--sidebar-width)',
          backgroundColor: 'var(--color-surface)',
          borderRight: '1px solid var(--color-border)',
          zIndex: 50,
          display: 'flex',
          flexDirection: 'column',
          transform: isOpen ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform var(--transition-normal)',
          boxShadow: isOpen ? 'var(--shadow-lg)' : 'none',
        }}
        className="sidebar"
        aria-label="Main Navigation"
      >
        {/* Mobile Header / Close */}
        <div
          style={{
            height: 'var(--header-height)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 var(--space-lg)',
            borderBottom: '1px solid var(--color-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
              }}
            >
              <Layers size={16} />
            </div>
            <span style={{ fontWeight: 800, fontSize: '1rem', letterSpacing: '-0.02em' }}>
              BQAS Menu
            </span>
          </div>

          <button
            onClick={onClose}
            className="btn btn-ghost"
            style={{ padding: '6px' }}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation Content */}
        <nav
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--space-md) var(--space-sm)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-xs)',
          }}
        >
          {/* Main Navigation Section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {/* 1. Drinks Accordion Header */}
            <div>
              <button
                onClick={() => setDrinksOpen(!drinksOpen)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  fontWeight: 600,
                  fontSize: '0.9375rem',
                  color: location.pathname.startsWith('/drinks')
                    ? 'var(--color-accent)'
                    : 'var(--color-text-main)',
                  backgroundColor: location.pathname.startsWith('/drinks')
                    ? 'var(--color-surface-dim)'
                    : 'transparent',
                  transition: 'background-color var(--transition-fast)',
                }}
                aria-expanded={drinksOpen}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <Layers size={18} />
                  <span>Drinks</span>
                </div>
                {drinksOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>

              {/* Drinks Submenu */}
              {drinksOpen && (
                <div
                  style={{
                    paddingLeft: '32px',
                    paddingTop: '4px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '2px',
                  }}
                >
                  {drinksSubmenu.map((sub) => {
                    const SubIcon = sub.icon;
                    const active = isActive(sub.path);
                    return (
                      <Link
                        key={sub.path}
                        to={sub.path}
                        onClick={() => {
                          if (window.innerWidth < 1024) onClose();
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px',
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.875rem',
                          fontWeight: active ? 600 : 400,
                          color: active ? 'var(--color-accent)' : 'var(--color-text-muted)',
                          backgroundColor: active ? 'var(--color-accent-subtle)' : 'transparent',
                        }}
                      >
                        <SubIcon size={16} />
                        <span>{sub.name}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>

            {/* 2. Lab */}
            <Link
              to="/lab"
              onClick={() => {
                if (window.innerWidth < 1024) onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                fontWeight: isActive('/lab') ? 600 : 500,
                fontSize: '0.9375rem',
                color: isActive('/lab') ? 'var(--color-accent)' : 'var(--color-text-main)',
                backgroundColor: isActive('/lab') ? 'var(--color-surface-dim)' : 'transparent',
              }}
            >
              <FlaskConical size={18} />
              <span>Lab</span>
            </Link>

            {/* 3. History */}
            <Link
              to="/history"
              onClick={() => {
                if (window.innerWidth < 1024) onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                fontWeight: isActive('/history') ? 600 : 500,
                fontSize: '0.9375rem',
                color: isActive('/history') ? 'var(--color-accent)' : 'var(--color-text-main)',
                backgroundColor: isActive('/history') ? 'var(--color-surface-dim)' : 'transparent',
              }}
            >
              <History size={18} />
              <span>History</span>
            </Link>

            {/* 4. About Us */}
            <Link
              to="/about"
              onClick={() => {
                if (window.innerWidth < 1024) onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                fontWeight: isActive('/about') ? 600 : 500,
                fontSize: '0.9375rem',
                color: isActive('/about') ? 'var(--color-accent)' : 'var(--color-text-main)',
                backgroundColor: isActive('/about') ? 'var(--color-surface-dim)' : 'transparent',
              }}
            >
              <Info size={18} />
              <span>About Us</span>
            </Link>
          </div>

          {/* Divider */}
          <div
            style={{
              height: '1px',
              backgroundColor: 'var(--color-border)',
              margin: 'var(--space-sm) 0',
            }}
          />

          {/* Secondary Navigation Section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {/* 5. Search */}
            <Link
              to="/search"
              onClick={() => {
                if (window.innerWidth < 1024) onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                fontWeight: isActive('/search') ? 600 : 500,
                fontSize: '0.9375rem',
                color: isActive('/search') ? 'var(--color-accent)' : 'var(--color-text-muted)',
                backgroundColor: isActive('/search') ? 'var(--color-surface-dim)' : 'transparent',
              }}
            >
              <Search size={18} />
              <span>Search</span>
            </Link>

            {/* 6. Account */}
            <Link
              to="/account"
              onClick={() => {
                if (window.innerWidth < 1024) onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                fontWeight: isActive('/account') ? 600 : 500,
                fontSize: '0.9375rem',
                color: isActive('/account') ? 'var(--color-accent)' : 'var(--color-text-muted)',
                backgroundColor: isActive('/account') ? 'var(--color-surface-dim)' : 'transparent',
              }}
            >
              <User size={18} />
              <span>Account</span>
            </Link>

            {/* 7. Settings */}
            <Link
              to="/settings"
              onClick={() => {
                if (window.innerWidth < 1024) onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                fontWeight: isActive('/settings') ? 600 : 500,
                fontSize: '0.9375rem',
                color: isActive('/settings') ? 'var(--color-accent)' : 'var(--color-text-muted)',
                backgroundColor: isActive('/settings') ? 'var(--color-surface-dim)' : 'transparent',
              }}
            >
              <Settings size={18} />
              <span>Settings</span>
            </Link>
          </div>
        </nav>

        {/* Footer Info in Sidebar */}
        <div
          style={{
            padding: 'var(--space-md)',
            borderTop: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-surface-container)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: 'var(--color-accent)',
              }}
            />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-main)' }}>
              Rules v1.0.0 · Data v1.0.0
            </span>
          </div>
          <p style={{ fontSize: '0.6875rem', color: 'var(--color-text-subtle)', lineHeight: 1.3 }}>
            WHO, EFSA, USDA & UCI Wine datasets verified.
          </p>
        </div>
      </aside>
    </>
  );
};
