"use client"

import { useEffect, useState } from "react"
import { Loader2, AlertCircle, RefreshCw } from "lucide-react"
import { apiUrl, type ConsolidatedItem } from "@/lib/api"
import { StoreSplitView } from "@/components/store-split-view"
import { KitchenStaplesModal } from "@/components/kitchen-staples-modal"

export function StoreLists() {
  const [items, setItems] = useState<ConsolidatedItem[]>([])
  const [kitchenStaples, setKitchenStaples] = useState<ConsolidatedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // State for controlling the modal
  const [showStaplesModal, setShowStaplesModal] = useState(false)

  const fetchItems = async () => {
    setLoading(true)
    setError(null)

    const endpoints = [
      "/grocery-list/current",
      "/grocery-list/consolidated",
      "/grocery-list",
    ]

    for (const path of endpoints) {
      try {
        const res = await fetch(apiUrl(path))
        if (res.ok) {
          const data = await res.json()
          setItems(Array.isArray(data) ? data : data.items || [])
          setKitchenStaples(data.kitchen_staples || [])
          setLoading(false)
          return
        }
      } catch {
        // Try the next endpoint if this route isn't mounted.
      }
    }

    setError("Could not connect to the grocery list endpoint. Is the FastAPI server running on port 8000?")
    setLoading(false)
  }

  useEffect(() => {
    fetchItems()
  }, [])

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">This Week&apos;s Route</h2>
          <p className="text-sm text-muted-foreground">
            Split by store &amp; aisle. Tap a store&apos;s{" "}
            <span className="font-medium text-foreground">copy</span> icon to paste it into a
            Google Keep checklist.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowStaplesModal(true)}
            className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm font-medium text-foreground transition hover:bg-secondary"
          >
            Show Kitchen Staples
            {kitchenStaples.length > 0 && (
              <span className="ml-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary font-semibold">
                {kitchenStaples.length}
              </span>
            )}
          </button>
          
          <button
            type="button"
            onClick={fetchItems}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm font-medium text-foreground transition hover:bg-secondary disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center gap-2 py-20 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin" /> Fetching store lists…
        </div>
      )}

      {error && !loading && (
        <div className="flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-foreground">
          <AlertCircle className="h-5 w-5 shrink-0 text-destructive" />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && <StoreSplitView items={items} onRefresh={fetchItems} />}

      {/* Kitchen Staples Modal */}
      <KitchenStaplesModal
        isOpen={showStaplesModal}
        onClose={() => setShowStaplesModal(false)}
        staples={kitchenStaples}
        onRefresh={fetchItems}
      />
    </div>
  )
}
