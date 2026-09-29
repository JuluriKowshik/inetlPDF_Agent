import { useRef, useState } from "react";
import { uploadPdf } from "../api.js";

export default function UploadZone({ onUploaded }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  async function handleFile(file) {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const doc = await uploadPdf(file);
      onUploaded(doc);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="px-4 pt-4">
      <button
        onClick={() => inputRef.current && inputRef.current.click()}
        disabled={uploading}
        className="w-full rounded-lg border border-dashed border-slate-700 px-3 py-4 text-sm text-slate-400 transition hover:border-amber-400/60 hover:text-slate-200 disabled:opacity-60"
      >
        {uploading ? "Indexing PDF..." : "Upload a PDF"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={(e) => handleFile(e.target.files && e.target.files[0])}
      />
      {error && <p className="mt-2 text-xs text-rose-400">{error}</p>}
    </div>
  );
}
