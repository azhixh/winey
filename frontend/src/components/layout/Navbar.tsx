import React from 'react';
import { Menu, Sun, Moon, Sparkles, Activity } from 'lucide-react';

interface NavbarProps {
  onToggleSidebar: () => void;
  theme: 'light' | 'dark' | 'system';
  onToggleTheme: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onToggleSidebar,
  theme,
  onToggleTheme,
}) => {
  return (
    <header
      className="glass-panel"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 40,
        height: 'var(--header-height)',
        display: 'flex',
        alignItems: 'center',
        borderBottom: '1px solid var(--color-border)',
        padding: '0 var(--space-lg)',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 'var(--max-content-width)',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Left: Hamburger & Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <button
            onClick={onToggleSidebar}
            className="btn btn-ghost"
            style={{ padding: '8px', borderRadius: 'var(--radius-sm)' }}
            aria-label="Toggle navigation menu"
          >
            <Menu size={22} />
          </button>

          <a href="/" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <Activity size={18} />
            </div>
            <div>
              <span
                style={{
                  fontFamily: 'var(--font-display)',
                  fontWeight: 800,
                  fontSize: '1.125rem',
                  letterSpacing: '-0.02em',
                  display: 'block',
                  lineHeight: 1.1,
                }}
              >
                BQAS
              </span>
              <span
                style={{
                  fontSize: '0.6875rem',
                  color: 'var(--color-text-subtle)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  fontWeight: 600,
                }}
              >
                Health-Tech Intelligence
              </span>
            </div>
          </a>
        </div>

        {/* Center: Live telemetry status indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--color-surface-dim)',
            padding: '4px 12px',
            borderRadius: 'var(--radius-pill)',
            border: '1px solid var(--color-border-subtle)',
          }}
          className="telemetry-pill"
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: 'var(--color-favourable)',
              display: 'inline-block',
            }}
          />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
            Step 6 Engine Live · Zero Null Imputation
          </span>
        </div>

        {/* Right: Theme Toggle & Quick Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
          <button
            onClick={onToggleTheme}
            className="btn btn-ghost"
            style={{ padding: '8px', borderRadius: 'var(--radius-sm)' }}
            aria-label="Toggle visual theme"
            title="Toggle theme (Light / Dark)"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>

          <a
            href="/lab"
            className="btn btn-primary"
            style={{
              padding: '6px 14px',
              fontSize: '0.8125rem',
              borderRadius: 'var(--radius-pill)',
            }}
          >
            <Sparkles size={14} />
            <span>New Analysis</span>
          </a>
        </div>
      </div>
    </header>
  );
};
