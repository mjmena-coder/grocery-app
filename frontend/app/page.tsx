"use client"

import { useState } from "react"
import { Upload, ShoppingBag, Link2, Sprout, BookOpen } from "lucide-react"
import { UploadRecipe } from "@/components/upload-recipe"
import { RecipesBrowser } from "@/components/recipes-browser"
import { StoreLists } from "@/components/store-lists"
import { UnlinkedIngredients } from "@/components/unlinked-ingredients"

type Tab = "recipes" | "upload" | "stores" | "unlinked"

const TABS: { id: Tab; label: string; icon: typeof Upload }[] = [
  { id: "recipes", label: "Recipes", icon: BookOpen },
  { id: "upload", label: "Upload", icon: Upload },
  { id: "stores", label: "Store Lists", icon: ShoppingBag },
  { id: "unlinked", label: "Unlinked", icon: Link2 },
]

export default function Page() {
  const [activeTab, setActiveTab] = useState<Tab>("recipes")

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
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        {activeTab === "recipes" && <RecipesBrowser onListGenerated={() => setActiveTab("stores")} />}
        {activeTab === "upload" && <UploadRecipe />}
        {activeTab === "stores" && <StoreLists />}
        {activeTab === "unlinked" && <UnlinkedIngredients />}
      </main>
    </div>
  )
}
