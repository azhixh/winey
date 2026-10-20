import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  User,
  Sparkles,
  History,
  Lock,
  CheckCircle2,
} from 'lucide-react';
import { getHistory } from '../services/historyService';

export const AccountPage: React.FC = () => {
  const [scanCount, setScanCount] = useState<number>(0);

  useEffect(() => {
    setScanCount(getHistory().length);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)', maxWidth: '840px', margin: '0 auto' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <User size={24} color="var(--color-accent)" />
          <h1>Account & Profile</h1>
        </div>
        <p>
          Beverage Quality Analysis System (BQAS) operates in local-first privacy mode. No account is required.
        </p>
      </div>

      {/* Guest Mode Status Card */}
      <section
        className="glass-panel"
        style={{
          padding: 'var(--space-xl)',
          borderRadius: 'var(--radius-xl)',
          borderLeft: '4px solid var(--color-favourable)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-2xs)' }}>
              <span className="badge badge-favourable">
                <CheckCircle2 size={14} /> Active Guest Session
              </span>
              <span className="badge badge-neutral">Offline Ready</span>
            </div>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '4px' }}>Private Local Workspace</h2>
            <p style={{ fontSize: '0.9375rem', lineHeight: 1.5, maxWidth: '580px' }}>
              Your laboratory evaluations, personalization parameters, and custom scans remain stored exclusively on your device in LocalStorage.
            </p>
          </div>

          <div
            style={{
              padding: 'var(--space-md) var(--space-lg)',
              backgroundColor: 'var(--color-surface-dim)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Saved Local Scans</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary)' }}>
              {scanCount}
            </div>
            <Link to="/history" style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-accent)' }}>
              View History →
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Capabilities Matrix */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <h3 style={{ marginBottom: 'var(--space-sm)' }}>Available Features in Guest Mode</h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)', marginBottom: 'var(--space-md)' }}>
          All PRD Section 12 scoring algorithms, reference ranges, and machine learning models are fully accessible without registration.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-md)' }}>
          <div style={{ padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface-dim)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', color: 'var(--color-favourable-text)' }}>
              <CheckCircle2 size={16} />
              <strong style={{ fontSize: '0.9375rem', color: 'var(--color-text-main)' }}>Interactive Lab Wizard</strong>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
              Full evaluation across all 5 beverage categories with zero synthetic zero-imputation.
            </p>
          </div>

          <div style={{ padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface-dim)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', color: 'var(--color-favourable-text)' }}>
              <CheckCircle2 size={16} />
              <strong style={{ fontSize: '0.9375rem', color: 'var(--color-text-main)' }}>Clinical Scoring Engine</strong>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
              Separated Health Impact and Composition scores with critical overrides and confidence levels.
            </p>
          </div>

          <div style={{ padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface-dim)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', color: 'var(--color-favourable-text)' }}>
              <CheckCircle2 size={16} />
              <strong style={{ fontSize: '0.9375rem', color: 'var(--color-text-main)' }}>Portuguese Wine ML Model</strong>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
              Sensory quality prediction using scikit-learn regressor trained on UCI Vinho Verde dataset.
            </p>
          </div>

          <div style={{ padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-surface-dim)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', color: 'var(--color-favourable-text)' }}>
              <CheckCircle2 size={16} />
              <strong style={{ fontSize: '0.9375rem', color: 'var(--color-text-main)' }}>PDF Export & Printing</strong>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
              Download clinical reports containing all charts, scores, citations, and disclaimers.
            </p>
          </div>
        </div>
      </section>

      {/* Cloud Synchronization Architecture Note */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-xs)' }}>
          <Lock size={18} color="var(--color-text-subtle)" />
          <h3>Cloud Authentication & Sync Status</h3>
        </div>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', lineHeight: 1.6, marginBottom: 'var(--space-md)' }}>
          In accordance with BQAS architectural principles, cloud authentication endpoints are not currently enabled on the backend server. We do not simulate fake login states or claim data is synced to cloud databases when it is preserved locally.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          <Link to="/lab" className="btn btn-primary" style={{ padding: '6px 14px', fontSize: '0.875rem' }}>
            <Sparkles size={14} />
            <span>Launch Lab Analysis</span>
          </Link>
          <Link to="/history" className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: '0.875rem' }}>
            <History size={14} />
            <span>Browse Saved Scans</span>
          </Link>
        </div>
      </section>
    </div>
  );
};
