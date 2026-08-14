import React, { useState, useEffect } from 'react';
import { Upload, ShoppingBag, Link2, AlertCircle, CheckCircle2, Loader2, FileImage } from 'lucide-react';
import { StoreSplitView, type ConsolidatedItem } from './components/StoreSplitView';

interface UnlinkedIngredient {
  id: number;
  raw_name: string;
  recipe_id: number;
  recipe_title?: string;
}

export function App() {
  const [activeTab, setActiveTab] = useState<'upload' | 'stores' | 'unlinked'>('upload');
  
  // Store List State
  const [consolidatedItems, setConsolidatedItems] = useState<ConsolidatedItem[]>([]);
  const [loadingStores, setLoadingStores] = useState<boolean>(false);
  const [storesError, setStoresError] = useState<string | null>(null);

  // Unlinked Ingredients State
  const [unlinkedItems, setUnlinkedItems] = useState<UnlinkedIngredient[]>([]);
  const [loadingUnlinked, setLoadingUnlinked] = useState<boolean>(false);

  // Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const getHost = () => window.location.hostname || 'localhost';

  // Fetch Current Grocery List
  const fetchConsolidatedItems = async () => {
    setLoadingStores(true);
    setStoresError(null);
    const host = getHost();
    
    const endpoints = [
      `http://${host}:8000/grocery-list/current`,
      `http://${host}:8000/grocery-list/consolidated`,
      `http://${host}:8000/grocery-list`
    ];

    for (const url of endpoints) {
      try {
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setConsolidatedItems(Array.isArray(data) ? data : data.items || []);
          setLoadingStores(false);
          return;
        }
      } catch {
        // Continue to next endpoint if route is not mounted
      }
    }

    setStoresError('Could not connect to grocery list endpoint.');
    setLoadingStores(false);
  };

  // Fetch Unlinked Ingredients
  const fetchUnlinked = async () => {
    setLoadingUnlinked(true);
    const host = getHost();
    try {
      const res = await fetch(`http://${host}:8000/canonical-ingredients/unlinked`);
      if (res.ok) {
        const data = await res.json();
        setUnlinkedItems(data);
      }
    } catch (err) {
      console.error('Failed to fetch unlinked ingredients:', err);
    } finally {
      setLoadingUnlinked(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'stores') fetchConsolidatedItems();
    if (activeTab === 'unlinked') fetchUnlinked();
  }, [activeTab]);

  // Handle Recipe Extraction Upload
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setUploadStatus(null);
    const host = getHost();

    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
      // Direct post to /recipes/extract endpoint
      const res = await fetch(`http://${host}:8000/recipes/extract`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `Server returned status ${res.status}`);
      }

      const data = await res.json();
      setUploadStatus({
        type: 'success',
        message: `Successfully extracted and saved recipe "${data.title || 'New Recipe'}"!`
      });
      setSelectedFile(null);
    } catch (err: any) {
      setUploadStatus({
        type: 'error',
        message: err.message || 'Failed to extract recipe.'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 font-sans text-gray-900">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-6 h-6 text-emerald-600" />
            <h1 className="font-bold text-xl text-gray-800">Grocery Assistant</h1>
          </div>

          <nav className="flex gap-2">
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'upload' ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Upload className="w-4 h-4" /> Upload Recipe
            </button>
            <button
              onClick={() => setActiveTab('stores')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'stores' ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <ShoppingBag className="w-4 h-4" /> Store Lists
            </button>
            <button
              onClick={() => setActiveTab('unlinked')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'unlinked' ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Link2 className="w-4 h-4" /> Unlinked Ingredients
            </button>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-6">
        {/* TAB 1: UPLOAD & VLM EXTRACTION */}
        {activeTab === 'upload' && (
          <div className="max-w-xl mx-auto bg-white p-8 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-xl font-bold mb-2">Upload Cookbook Photo</h2>
            <p className="text-sm text-gray-500 mb-6">
              Posts image to <code className="text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded font-mono">POST /recipes/extract</code> for VLM scanning &amp; store assignment.
            </p>

            <form onSubmit={handleUpload} className="space-y-6">
              <div className="border-2 border-dashed border-gray-300 hover:border-emerald-500 rounded-xl p-8 text-center bg-gray-50 hover:bg-emerald-50/30 transition cursor-pointer relative">
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <FileImage className="w-10 h-10 mx-auto text-gray-400 mb-2" />
                {selectedFile ? (
                  <p className="font-semibold text-emerald-700">{selectedFile.name}</p>
                ) : (
                  <div>
                    <p className="font-medium text-gray-700">Click or drag recipe image here</p>
                    <p className="text-xs text-gray-400 mt-1">Supports JPG, PNG, WEBP</p>
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={!selectedFile || uploading}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" /> Scanning with Qwen2.5-VL...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" /> Extract Recipe
                  </>
                )}
              </button>
            </form>

            {uploadStatus && (
              <div
                className={`mt-6 p-4 rounded-lg flex items-center gap-3 ${
                  uploadStatus.type === 'success'
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}
              >
                {uploadStatus.type === 'success' ? (
                  <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
                )}
                <span className="text-sm">{uploadStatus.message}</span>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: STORE LISTS */}
        {activeTab === 'stores' && (
          <div>
            {loadingStores && (
              <div className="flex items-center justify-center py-16 gap-2 text-gray-500">
                <Loader2 className="w-6 h-6 animate-spin" /> Fetching store lists...
              </div>
            )}

            {storesError && (
              <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg flex items-center gap-2">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>{storesError}</span>
              </div>
            )}

            {!loadingStores && !storesError && <StoreSplitView items={consolidatedItems} />}
          </div>
        )}

        {/* TAB 3: UNLINKED INGREDIENTS */}
        {activeTab === 'unlinked' && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-xl font-bold mb-1">Unlinked Ingredients</h2>
            <p className="text-sm text-gray-500 mb-6">
              Ingredients fetched from <code className="text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded font-mono">GET /canonical-ingredients/unlinked</code> needing dictionary mapping.
            </p>

            {loadingUnlinked ? (
              <div className="flex items-center justify-center py-12 gap-2 text-gray-500">
                <Loader2 className="w-5 h-5 animate-spin" /> Checking unlinked items...
              </div>
            ) : unlinkedItems.length === 0 ? (
              <p className="text-sm text-gray-400 italic text-center py-8">All ingredients are linked cleanly!</p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {unlinkedItems.map((item) => (
                  <li key={item.id} className="py-3 flex justify-between items-center">
                    <span className="font-medium text-gray-800">{item.raw_name}</span>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full">
                      Recipe #{item.recipe_id}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;