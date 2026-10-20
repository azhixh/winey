import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  History,
  Trash2,
  Calendar,
  Sparkles,
  ArrowRight,
  Filter,
  ArrowUpDown,
  FileText,
} from 'lucide-react';
import {
  getHistory,
  deleteHistoryItem,
  clearHistory,
} from '../services/historyService';
import type { HistoryRecord, BeverageCategory } from '../types';

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [historyItems, setHistoryItems] = useState<HistoryRecord[]>([]);
  const [filterCategory, setFilterCategory] = useState<string>('All');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [showClearConfirm, setShowClearConfirm] = useState<boolean>(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = () => {
    setHistoryItems(getHistory());
  };

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    deleteHistoryItem(id);
    loadHistory();
  };

  const handleClearAll = () => {
    clearHistory();
    loadHistory();
    setShowClearConfirm(false);
  };

  // Filter & sort
  const filteredItems = historyItems
    .filter((item) => {
      if (filterCategory === 'All') return true;
      return item.beverage_type === filterCategory;
    })
    .sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime();
      const timeB = new Date(b.timestamp).getTime();
      return sortOrder === 'desc' ? timeB - timeA : timeA - timeB;
    });

  const categories: (BeverageCategory | 'All')[] = [
    'All',
    'Soft drink',
    'Beer',
    'Wine',
    'Spirits',
    'Energy drink',
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <History size={24} color="var(--color-accent)" />
            <h1>Scan & Analysis History</h1>
          </div>
          <p>
            Local-first records stored on this device. Reports remain viewable offline with original rules and dataset versions.
          </p>
        </div>

        {historyItems.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
            {showClearConfirm ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.8125rem', color: 'var(--color-critical-text)', fontWeight: 600 }}>
                  Confirm delete all?
                </span>
                <button
                  onClick={handleClearAll}
                  className="btn btn-primary"
                  style={{ backgroundColor: 'var(--color-critical)', padding: '6px 12px', fontSize: '0.8125rem' }}
                >
                  Yes, Clear All
                </button>
                <button
                  onClick={() => setShowClearConfirm(false)}
                  className="btn btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '0.8125rem' }}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowClearConfirm(true)}
                className="btn btn-secondary"
                style={{ padding: '6px 14px', fontSize: '0.8125rem', color: 'var(--color-critical-text)' }}
              >
                <Trash2 size={14} />
                <span>Clear All History</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Filter and Sort Toolbar */}
      {historyItems.length > 0 && (
        <div
          className="card"
          style={{
            padding: 'var(--space-sm) var(--space-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 'var(--space-sm)',
          }}
        >
          {/* Category Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <Filter size={16} color="var(--color-text-subtle)" />
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
              Category:
            </span>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setFilterCategory(cat)}
                className={`btn ${filterCategory === cat ? 'btn-primary' : 'btn-ghost'}`}
                style={{ padding: '4px 10px', fontSize: '0.8125rem', borderRadius: 'var(--radius-pill)' }}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Sort Order Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              className="btn btn-ghost"
              style={{ padding: '4px 8px', fontSize: '0.8125rem' }}
            >
              <ArrowUpDown size={14} />
              <span>Date: {sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}</span>
            </button>
          </div>
        </div>
      )}

      {/* History Items List */}
      {filteredItems.length === 0 ? (
        <div className="card" style={{ padding: 'var(--space-2xl)', textAlign: 'center' }}>
          <FileText size={48} color="var(--color-text-subtle)" style={{ margin: '0 auto var(--space-md)' }} />
          <h2 style={{ marginBottom: 'var(--space-xs)' }}>
            {historyItems.length === 0 ? 'No drinks scanned yet' : 'No matching drinks in this category'}
          </h2>
          <p style={{ maxWidth: '480px', margin: '0 auto var(--space-lg)' }}>
            {historyItems.length === 0
              ? 'Analyze packaged sodas, beers, wines, spirits, or energy drinks in the Lab. Your evidence-based evaluations will appear here.'
              : 'Try selecting "All" or a different category above.'}
          </p>
          <Link to="/lab" className="btn btn-primary">
            <Sparkles size={16} />
            <span>Analyze a Beverage in the Lab</span>
          </Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          {filteredItems.map((item) => (
            <div
              key={item.id}
              onClick={() => navigate(`/result?id=${item.id}`)}
              className="card"
              style={{
                padding: 'var(--space-md) var(--space-lg)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 'var(--space-md)',
                cursor: 'pointer',
                transition: 'border-color var(--transition-fast), box-shadow var(--transition-fast)',
              }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="badge badge-neutral">{item.beverage_type}</span>
                  {item.is_critical && (
                    <span className="badge badge-critical">Critical Override</span>
                  )}
                  <span className={`badge ${item.confidence_level === 'High' ? 'badge-favourable' : 'badge-moderate'}`}>
                    {item.confidence_level} Conf.
                  </span>
                </div>

                <h3 style={{ fontSize: '1.125rem' }}>{item.product_name}</h3>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
                  <span>Serving: <strong>{item.serving_size_ml} mL</strong></span>
                  <span>·</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Calendar size={12} /> {new Date(item.timestamp).toLocaleString()}
                  </span>
                  <span>·</span>
                  <span>Rules v{item.rules_version} · Data v{item.dataset_version}</span>
                </div>
              </div>

              {/* Scores Cluster */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xl)' }}>
                {/* Health Score */}
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--color-text-subtle)', display: 'block' }}>
                    Health Score
                  </span>
                  <strong style={{ fontSize: '1.375rem', color: 'var(--color-primary)' }}>
                    {item.health_impact_score !== null && item.health_impact_score !== undefined
                      ? item.health_impact_score.toFixed(0)
                      : '—'}
                  </strong>
                </div>

                {/* Comp Score */}
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--color-text-subtle)', display: 'block' }}>
                    Comp Score
                  </span>
                  <strong style={{ fontSize: '1.375rem', color: 'var(--color-accent)' }}>
                    {item.composition_score !== null && item.composition_score !== undefined
                      ? item.composition_score.toFixed(0)
                      : '—'}
                  </strong>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-accent)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    View Report <ArrowRight size={14} />
                  </span>

                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="btn btn-ghost"
                    style={{ padding: '6px', color: 'var(--color-text-subtle)' }}
                    aria-label="Delete saved report"
                    title="Delete saved report"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
