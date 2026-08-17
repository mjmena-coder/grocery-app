"use client"

import { useEffect, useState } from "react"
import { Loader2, Link2, CheckCircle2, AlertCircle } from "lucide-react"
import { apiUrl, type UnlinkedIngredient } from "@/lib/api"

export function UnlinkedIngredients() {
  const [items, setItems] = useState<UnlinkedIngredient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchUnlinked = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(apiUrl("/canonical-ingredients/unlinked"))
      if (!res.ok) throw new Error(`Server returned status ${res.status}`)
      const data = await res.json()
      setItems(Array.isArray(data) ? data : data.items || [])
    } catch {
      setError("Could not reach the canonical-ingredients endpoint on port 8000.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUnlinked()
  }, [])

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h2 className="font-display text-xl font-semibold text-foreground">Unlinked Ingredients</h2>
        <p className="text-sm text-muted-foreground">
          Raw entries from{" "}
          <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-xs text-primary">
            GET /canonical-ingredients/unlinked
          </code>{" "}
          that still need dictionary mapping.
        </p>
      </div>

      <div className="rounded-2xl border border-border bg-card shadow-sm">
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" /> Checking unlinked items…
          </div>
        ) : error ? (
          <div className="flex items-start gap-3 p-5 text-sm text-foreground">
            <AlertCircle className="h-5 w-5 shrink-0 text-destructive" />
            <span>{error}</span>
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <CheckCircle2 className="mb-3 h-8 w-8 text-primary" />
            <p className="font-display font-semibold text-foreground">All ingredients are linked</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Every raw entry maps cleanly to a canonical item.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {items.map((item) => (
              <li key={item.id} className="flex items-center justify-between gap-3 px-5 py-3.5">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/20 text-accent-foreground">
                    <Link2 className="h-4 w-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate font-medium text-foreground">{item.raw_name}</p>
                    {item.recipe_title && (
                      <p className="truncate text-xs text-muted-foreground">{item.recipe_title}</p>
                    )}
                  </div>
                </div>
                <span className="shrink-0 rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-muted-foreground">
                  Recipe #{item.recipe_id}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
