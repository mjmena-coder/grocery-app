"use client"

import { useState, useEffect, useRef } from "react"
import { Upload, ShoppingBag, Link2, Sprout, BookOpen, Loader2, CheckCircle2, X } from "lucide-react"
import { UploadRecipe } from "@/components/upload-recipe"
import { RecipesBrowser } from "@/components/recipes-browser"
import { StoreLists } from "@/components/store-lists"
import { UnlinkedIngredients } from "@/components/unlinked-ingredients"
import { apiUrl } from "@/lib/api"

type Tab = "recipes" | "upload" | "stores" | "unlinked"

const TABS: { id: Tab; label: string; icon: typeof Upload }[] = [
  { id: "recipes", label: "Recipes", icon: BookOpen },
  { id: "upload", label: "Upload", icon: Upload },
  { id: "stores", label: "Store Lists", icon: ShoppingBag },
  { id: "unlinked", label: "Unlinked", icon: Link2 },
]

interface ExtractionStatus {
  is_busy: boolean
  filename?: string | null
  started_at?: number | null
  last_completed_recipe?: { recipe_id?: number; title?: string } | null
  last_completed_at?: number | null
}

export default function Page() {
  const [activeTab, setActiveTab] = useState<Tab>("recipes")
  const [extractionStatus, setExtractionStatus] = useState<ExtractionStatus>({ is_busy: false })
  const [toast, setToast] = useState<{ title: string; recipeId?: number } | null>(null)
  const lastSeenCompletedAt = useRef<number | null>(null)

  const checkStatus = async () => {
    try {
      const res = await fetch(apiUrl("/recipes/extract/status"))
      if (!res.ok) return
      const data: ExtractionStatus = await res.json()
      setExtractionStatus(data)

      if (
        data.last_completed_at &&
        data.last_completed_recipe &&
        (!lastSeenCompletedAt.current || data.last_completed_at > lastSeenCompletedAt.current)
      ) {
        if (lastSeenCompletedAt.current !== null) {
          setToast({
            title: data.last_completed_recipe.title || "New Recipe",
            recipeId: data.last_completed_recipe.recipe_id,
          })
        }
        lastSeenCompletedAt.current = data.last_completed_at
      }
    } catch {
      // Ignore network errors during polling
    }
  }

  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 3000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-border bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Sprout className="h-5 w-5" />
            </span>
            <div className="leading-tight">
              <h1 className="font-display text-lg font-semibold text-foreground">Grocery Assistant</h1>
              <p className="hidden text-xs text-muted-foreground sm:block">Recipe &amp; store router</p>
            </div>
          </div>

          <nav className="flex items-center gap-1 rounded-xl border border-border bg-card p-1">
            {TABS.map((tab) => {
              const Icon = tab.icon
              const active = activeTab === tab.id
              const isUploadBusy = tab.id === "upload" && extractionStatus.is_busy

              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                    active
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  }`}
                >
                  {isUploadBusy ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                  <span className="hidden sm:inline">{tab.label}</span>
                  {isUploadBusy && (
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
                    </span>
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        {extractionStatus.is_busy && (
          <div className="border-t border-primary/20 bg-primary/10 px-4 py-2 text-xs font-medium text-primary">
            <div className="mx-auto flex max-w-5xl items-center justify-between">
              <div className="flex items-center gap-2">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>
                  Scanning cookbook page with Qwen2.5-VL
                  {extractionStatus.filename ? ` (${extractionStatus.filename})` : ""}…
                </span>
              </div>
              <button
                type="button"
                onClick={() => setActiveTab("upload")}
                className="underline hover:text-foreground"
              >
                View status
              </button>
            </div>
          </div>
        )}
      </header>

      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex max-w-sm items-center gap-3 rounded-xl border border-primary/30 bg-card p-4 shadow-lg">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-primary" />
          <div className="flex-1 text-sm">
            <p className="font-semibold text-foreground">Extraction Complete</p>
            <p className="text-xs text-muted-foreground line-clamp-1">
              &ldquo;{toast.title}&rdquo; is ready.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setToast(null)
              setActiveTab("recipes")
            }}
            className="rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary hover:bg-primary/20"
          >
            View
          </button>
          <button
            type="button"
            onClick={() => setToast(null)}
            className="text-muted-foreground hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <main className="mx-auto max-w-5xl px-4 py-8">
        {activeTab === "recipes" && <RecipesBrowser onListGenerated={() => setActiveTab("stores")} />}
        {activeTab === "upload" && (
          <UploadRecipe
            isBusy={extractionStatus.is_busy}
            busyFilename={extractionStatus.filename}
            onUploadStarted={checkStatus}
            onUploadFinished={checkStatus}
          />
        )}
        {activeTab === "stores" && <StoreLists />}
        {activeTab === "unlinked" && <UnlinkedIngredients />}
      </main>
    </div>
  )
}
