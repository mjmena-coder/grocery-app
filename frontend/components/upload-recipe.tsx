"use client"

import { useState, type FormEvent } from "react"
import {
  Upload,
  Loader2,
  FileImage,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Camera,
} from "lucide-react"
import { apiUrl, uploadRecipePhoto } from "@/lib/api"

export function UploadRecipe() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [status, setStatus] = useState<{
    type: "success" | "error"
    message: string
    recipeId?: number
  } | null>(null)
  const [uploadingPhoto, setUploadingPhoto] = useState(false)

  const onSelect = (file: File | null) => {
    setSelectedFile(file)
    setStatus(null)
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(file ? URL.createObjectURL(file) : null)
  }

  const handleUpload = async (e: FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return

    setUploading(true)
    setStatus(null)

    const formData = new FormData()
    // Uses correct upload type (image).
    formData.append("image", selectedFile)

    // Image entry acquired and checked, time to POST to 'extract' endpoint.
    try {
      const res = await fetch(apiUrl("/recipes/extract"), {
        method: "POST",
        body: formData,
      })
      if (!res.ok) {
        // Return error.
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail || `Server returned status ${res.status}`)
      }
      const data = await res.json()
      setStatus({
        type: "success",
        message: `Extracted and saved "${data.title || "New Recipe"}".`,
        recipeId: data.recipe_id,
      })
      // Runs function to clear selected file after successful extraction.
      onSelect(null)
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to extract recipe.",
      })
    } finally {
      // Always return uploading block to false regardless (probably).
      setUploading(false)
    }
  }

  const handleAttachPhoto = async (file: File | null) => {
    if (!file || !status?.recipeId) return
    setUploadingPhoto(true)
    try {
      await uploadRecipePhoto(status.recipeId, file)
      setStatus({
        type: "success",
        message: `Updated photo for recipe.`,
        recipeId: status.recipeId,
      })
    } catch (err) {
      setStatus((prev) =>
        prev
          ? {
              ...prev,
              message: err instanceof Error ? err.message : "Failed to upload photo.",
            }
          : null
      )
    } finally {
      setUploadingPhoto(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <div className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
        <Sparkles className="h-4 w-4 text-primary" />
        <span>
          Posts to{" "}
          <code className="rounded bg-secondary px-1.5 py-0.5 font-mono text-xs text-primary">
            POST /recipes/extract
          </code>{" "}
          for VLM scanning &amp; store assignment.
        </span>
      </div>

      <form
        onSubmit={handleUpload}
        className="rounded-2xl border border-border bg-card p-6 shadow-sm"
      >
        <label className="relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border bg-secondary/40 px-6 py-12 text-center transition hover:border-primary hover:bg-secondary">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => onSelect(e.target.files?.[0] || null)}
            className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
            aria-label="Upload cookbook photo"
          />
          {previewUrl ? (
            <img
              src={previewUrl || "/placeholder.svg"}
              alt="Selected recipe preview"
              className="mb-3 h-40 w-auto max-w-full rounded-lg object-cover shadow-sm"
              crossOrigin="anonymous"
            />
          ) : (
            <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-card">
              <FileImage className="h-6 w-6 text-muted-foreground" />
            </div>
          )}
          {selectedFile ? (
            <p className="font-medium text-primary">{selectedFile.name}</p>
          ) : (
            <>
              <p className="font-display font-semibold text-foreground">
                Click or drop a recipe photo
              </p>
              <p className="mt-1 text-xs text-muted-foreground">JPG, PNG, or WEBP</p>
            </>
          )}
        </label>

        <button
          type="submit"
          disabled={!selectedFile || uploading}
          className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 font-semibold text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {uploading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" /> Scanning with Qwen2.5-VL…
            </>
          ) : (
            <>
              <Upload className="h-5 w-5" /> Extract Recipe
            </>
          )}
        </button>

        {status && (
          <div
            role="status"
            className={`mt-5 flex flex-col gap-3 rounded-xl border p-4 text-sm ${
              status.type === "success"
                ? "border-primary/30 bg-primary/5 text-foreground"
                : "border-destructive/30 bg-destructive/5 text-foreground"
            }`}
          >
            <div className="flex items-start gap-3">
              {status.type === "success" ? (
                <CheckCircle2 className="h-5 w-5 shrink-0 text-primary" />
              ) : (
                <AlertCircle className="h-5 w-5 shrink-0 text-destructive" />
              )}
              <span>{status.message}</span>
            </div>

            {status.type === "success" && status.recipeId && (
              <div className="mt-1 flex items-center gap-2 border-t border-border/40 pt-3">
                <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-card px-3 py-1.5 text-xs font-semibold text-foreground shadow-sm transition hover:bg-secondary">
                  <Camera className="h-4 w-4 text-primary" />
                  {uploadingPhoto ? "Uploading Photo..." : "Add / Update Photo"}
                  <input
                    type="file"
                    accept="image/*"
                    disabled={uploadingPhoto}
                    onChange={(e) => handleAttachPhoto(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                </label>
              </div>
            )}
          </div>
        )}
      </form>
    </div>
  )
}
