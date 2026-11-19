"use client";

import { useEffect, useState } from "react";
import { fileUrl } from "@/lib/api";

/** Shows a protected original document. The original is displayed, never modified. */
export function DocViewer({ path, alt }: { path: string | null; alt: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  useEffect(() => {
    if (!path) return;
    let revoke: string | null = null;
    fileUrl(path).then((u) => { revoke = u; setUrl(u); }).catch((e) => setError(e.message));
    return () => { if (revoke) URL.revokeObjectURL(revoke); };
  }, [path]);
  if (!path) return <p className="text-sm text-ink-soft">No file was attached.</p>;
  if (error) return <p className="text-sm text-differ">{error}</p>;
  if (!url) return <p className="text-sm text-ink-soft">Loading original…</p>;
  return (
    <div className="space-y-2">
      <div className="flex gap-2 text-xs">
        <button className="border border-rule rounded px-2 py-1" onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}>−</button>
        <span className="py-1 tabular-nums">{Math.round(zoom * 100)}%</span>
        <button className="border border-rule rounded px-2 py-1" onClick={() => setZoom((z) => Math.min(3, z + 0.25))}>+</button>
        <a href={url} target="_blank" rel="noreferrer" className="underline py-1 ml-auto">Open full size</a>
      </div>
      <div className="overflow-auto border border-rule rounded bg-paper max-h-[70vh]">
        {/* eslint-disable-next-line @next/next/no-img-element -- protected blob URL */}
        <img src={url} alt={alt} style={{ width: `${zoom * 100}%`, maxWidth: "none" }} />
      </div>
    </div>
  );
}
