import { useState, useCallback } from "react";
import { CloudUpload, FileText, ScanLine, X, Loader2, CheckCircle2 } from "lucide-react";
import type { UploadResult } from "../types";
import { uploadFile } from "../api";

interface Props {
  label: string;
  description: string;
  docType: string;
  accept: string;
  onUploaded: (result: UploadResult) => void;
}

export default function FileUpload({
  label,
  description,
  docType,
  accept,
  onUploaded,
}: Props) {
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

  const clear = () => {
    setResult(null);
    setError(null);
  };

  if (result) {
    return (
      <div className="animate-fade-in rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-green-50 p-5">
        <div className="flex items-start gap-4">
          <div className="relative shrink-0">
            <img
              src={result.preview_url}
              alt="Preview"
              className="w-16 h-22 object-cover rounded-xl border border-white shadow-md"
            />
            <CheckCircle2
              size={20}
              className="absolute -bottom-1.5 -right-1.5 text-emerald-500 bg-white rounded-full"
            />
          </div>
          <div className="flex-1 min-w-0 pt-0.5">
            <p className="font-semibold text-gray-900 text-sm truncate">
              {result.filename}
            </p>
            <p className="text-xs text-emerald-600 mt-1 font-medium">
              Detected as{" "}
              <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-bold uppercase tracking-wide">
                {result.doc_type}
              </span>
            </p>
          </div>
          <button
            onClick={clear}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
          >
            <X size={16} />
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
      className={`group relative rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-200 cursor-pointer ${
        dragging
          ? "border-brand-500 bg-brand-50 scale-[1.02]"
          : "border-gray-200 hover:border-brand-300 hover:bg-brand-50/30 bg-white"
      }`}
    >
      <input
        type="file"
        accept={accept}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />

      {uploading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-brand-50 flex items-center justify-center">
            <Loader2 className="animate-spin text-brand-600" size={26} />
          </div>
          <div>
            <p className="text-sm font-semibold text-brand-700">Processing...</p>
            <p className="text-xs text-gray-400 mt-0.5">Analyzing document</p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-gray-50 group-hover:bg-brand-50 flex items-center justify-center transition-colors">
            {docType === "passport" ? (
              <ScanLine
                size={26}
                className="text-gray-400 group-hover:text-brand-600 transition-colors"
              />
            ) : (
              <FileText
                size={26}
                className="text-gray-400 group-hover:text-brand-600 transition-colors"
              />
            )}
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-700">{label}</p>
            <p className="text-xs text-gray-400 mt-0.5">{description}</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-brand-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
            <CloudUpload size={14} />
            Drop file or click to browse
          </div>
        </div>
      )}

      {error && (
        <p className="mt-3 text-xs text-red-600 font-medium">{error}</p>
      )}
    </div>
  );
}
