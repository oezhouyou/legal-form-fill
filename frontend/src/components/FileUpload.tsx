import { useState, useCallback } from "react";
import { Upload, FileText, Image, X, Loader2 } from "lucide-react";
import type { UploadResult } from "../types";
import { uploadFile } from "../api";

interface Props {
  label: string;
  docType: string;
  accept: string;
  onUploaded: (result: UploadResult) => void;
}

export default function FileUpload({ label, docType, accept, onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setUploading(true);
      setError(null);
      try {
        const res = await uploadFile(file, docType);
        setResult(res);
        onUploaded(res);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [docType, onUploaded]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const clear = () => {
    setResult(null);
    setError(null);
  };

  if (result) {
    return (
      <div className="border border-green-200 bg-green-50 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <img
            src={result.preview_url}
            alt="Preview"
            className="w-20 h-28 object-cover rounded border shadow-sm"
          />
          <div className="flex-1 min-w-0">
            <p className="font-medium text-green-800 truncate">{result.filename}</p>
            <p className="text-sm text-green-600 mt-1">
              Detected as: <span className="font-semibold uppercase">{result.doc_type}</span>
            </p>
          </div>
          <button onClick={clear} className="text-gray-400 hover:text-red-500">
            <X size={18} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
        dragging
          ? "border-blue-500 bg-blue-50"
          : "border-gray-300 hover:border-gray-400 bg-white"
      }`}
    >
      <input
        type="file"
        accept={accept}
        onChange={onInputChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />

      {uploading ? (
        <div className="flex flex-col items-center gap-2 text-blue-600">
          <Loader2 className="animate-spin" size={32} />
          <span className="text-sm font-medium">Uploading...</span>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 text-gray-500">
          <div className="flex gap-2">
            {docType === "passport" ? <Image size={28} /> : <FileText size={28} />}
            <Upload size={28} />
          </div>
          <p className="font-medium text-gray-700">{label}</p>
          <p className="text-xs text-gray-400">
            Drag & drop or click to browse. PDF, JPG, PNG accepted.
          </p>
        </div>
      )}

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
