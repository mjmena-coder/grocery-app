import React, { useState } from 'react';
import { Copy, Check, ShoppingBag, Store } from 'lucide-react';

export interface ConsolidatedItem {
  id: number;
  canonical_name: string;
  quantity_display: string | null;
  category: string;
  assigned_store: 'King Soopers' | 'Whole Foods';
}

interface StoreSplitViewProps {
  items: ConsolidatedItem[];
}

export const StoreSplitView: React.FC<StoreSplitViewProps> = ({ items }) => {
  const [copiedStore, setCopiedStore] = useState<string | null>(null);

  const stores = ['King Soopers', 'Whole Foods'] as const;

  const getKeepTextForStore = (storeName: string) => {
    return items
      .filter((item) => item.assigned_store === storeName)
      .map((item) => {
        const name = item.canonical_name.charAt(0).toUpperCase() + item.canonical_name.slice(1);
        return item.quantity_display ? `${name} (${item.quantity_display})` : name;
      })
      .join('\n');
  };

  const handleCopy = (storeName: string) => {
    const text = getKeepTextForStore(storeName);
    navigator.clipboard.writeText(text);
    setCopiedStore(storeName);
    setTimeout(() => setCopiedStore(null), 2000);
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '16px', fontFamily: 'sans-serif' }}>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#1f2937' }}>
        <ShoppingBag color="#059669" />
        Weekly Store Lists
      </h2>

      {stores.map((store) => {
        const storeItems = items.filter((i) => i.assigned_store === store);
        if (storeItems.length === 0) return null;

        const keepText = getKeepTextForStore(store);

        return (
          <div key={store} style={{ border: '1px solid #e5e7eb', borderRadius: '12px', marginBottom: '20px', overflow: 'hidden' }}>
            <div style={{ backgroundColor: '#f9fafb', padding: '12px 16px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Store color="#4b5563" size={20} />
                <strong style={{ fontSize: '18px', color: '#111827' }}>{store}</strong>
                <span style={{ fontSize: '12px', background: '#e5e7eb', padding: '2px 8px', borderRadius: '12px' }}>
                  {storeItems.length} items
                </span>
              </div>

              <button
                onClick={() => handleCopy(store)}
                style={{
                  backgroundColor: copiedStore === store ? '#059669' : '#10b981',
                  color: '#ffffff',
                  border: 'none',
                  padding: '8px 14px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: '600'
                }}
              >
                {copiedStore === store ? <Check size={16} /> : <Copy size={16} />}
                {copiedStore === store ? 'Copied!' : 'Copy to Keep'}
              </button>
            </div>

            <div style={{ backgroundColor: '#111827', color: '#34d399', padding: '16px', fontFamily: 'monospace', fontSize: '14px' }}>
              <pre style={{ margin: 0, whitespace: 'pre-wrap' }}>{keepText}</pre>
            </div>
          </div>
        );
      })}
    </div>
  );
};