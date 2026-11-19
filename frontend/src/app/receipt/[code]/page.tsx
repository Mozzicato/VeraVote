"use client";

import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Receipt } from "@/lib/types";
import { ReceiptCard } from "@/components/ReceiptCard";
import { ErrorText, Loading } from "@/components/ui";

export default function ReceiptPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params);
  const [r, setR] = useState<Receipt | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Receipt>(`/public/receipts/${encodeURIComponent(code)}`).then(setR).catch((e) => setError(e.message));
  }, [code]);
  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold">Submission status</h1>
      <ErrorText error={error} />
      {!r && !error ? <Loading /> : r && <ReceiptCard r={r} />}
    </div>
  );
}
