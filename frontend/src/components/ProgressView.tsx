import { useMemo, useRef, useEffect } from "react";
import {
  Check,
  Loader2,
  AlertCircle,
  Image,
  CheckCircle2,
  XCircle,
  Sparkles,
} from "lucide-react";
import type { FormFillProgress, FormFillResult } from "../types";
import { screenshotUrl } from "../api";

interface Props {
  items: FormFillProgress[];
  result: FormFillResult | null;
}

export default function ProgressView({ items, result }: Props) {
  const latestProgress =
    items.length > 0 ? items[items.length - 1].progress : 0;
  const logRef = useRef<HTMLDivElement>(null);

  const fields = useMemo(() => {
    const map = new Map<string, FormFillProgress>();
    for (const item of items) {
      map.set(item.field, item);
    }
    return Array.from(map.values());
  }, [items]);

  // Auto-scroll the log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [fields]);

  const pct = Math.round(latestProgress);

  return (
    <div className="space-y-6">
      {/* Progress header */}
      <div className="flex items-center gap-4">
        <div className="relative w-16 h-16 shrink-0">
          <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
            <circle
              cx="32"
              cy="32"
              r="28"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="5"
            />
            <circle
              cx="32"
              cy="32"
              r="28"
              fill="none"
              stroke={result ? (result.success ? "#10b981" : "#ef4444") : "#3b82f6"}
              strokeWidth="5"
              strokeLinecap="round"
              strokeDasharray={`${(pct / 100) * 175.9} 175.9`}
              className="transition-all duration-500"
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-700">
            {pct}%
          </span>
        </div>
        <div className="flex-1">
          <p className="font-semibold text-gray-900">
            {result
              ? result.success
                ? "Form Filled Successfully"
                : "Completed with Errors"
              : "Filling Form..."}
          </p>
          <p className="text-sm text-gray-500 mt-0.5">
            {result
              ? `${result.filled_fields} of ${result.total_fields} fields populated`
              : `${fields.filter((f) => f.status === "done").length} fields completed`}
          </p>
        </div>
        {!result && (
          <Sparkles size={20} className="text-brand-500 animate-pulse-soft" />
        )}
      </div>

      {/* Linear progress bar */}
      <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            result
              ? result.success
                ? "bg-emerald-500"
                : "bg-red-400"
              : "bg-brand-600"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Field log */}
      <div
        ref={logRef}
        className="max-h-56 overflow-y-auto rounded-xl border border-gray-100 bg-gray-50/50"
      >
        {fields.map((item, i) => (
          <div
            key={item.field}
            className={`flex items-center gap-3 px-4 py-2.5 text-sm animate-slide-in ${
              i < fields.length - 1 ? "border-b border-gray-100" : ""
            }`}
          >
            {item.status === "filling" && (
              <Loader2
                size={15}
                className="text-brand-500 animate-spin shrink-0"
              />
            )}
            {item.status === "done" && (
              <Check
                size={15}
                className="text-emerald-500 shrink-0"
              />
            )}
            {item.status === "error" && (
              <AlertCircle size={15} className="text-red-500 shrink-0" />
            )}
            <span className="font-mono text-xs text-gray-600 truncate flex-1">
              {item.field.replace(/\./g, " > ")}
            </span>
            <span
              className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                item.status === "done"
                  ? "bg-emerald-50 text-emerald-600"
                  : item.status === "filling"
                    ? "bg-brand-50 text-brand-600"
                    : "bg-red-50 text-red-600"
              }`}
            >
              {item.status === "done"
                ? "filled"
                : item.status === "filling"
                  ? "filling"
                  : "error"}
            </span>
          </div>
        ))}
      </div>

      {/* Result card */}
      {result && (
        <div
          className={`animate-fade-in rounded-2xl p-6 ${
            result.success
              ? "bg-gradient-to-br from-emerald-50 to-green-50 border border-emerald-200"
              : "bg-gradient-to-br from-red-50 to-orange-50 border border-red-200"
          }`}
        >
          <div className="flex items-center gap-3 mb-3">
            {result.success ? (
              <CheckCircle2 size={24} className="text-emerald-500" />
            ) : (
              <XCircle size={24} className="text-red-500" />
            )}
            <div>
              <p
                className={`font-bold ${
                  result.success ? "text-emerald-800" : "text-red-800"
                }`}
              >
                {result.success
                  ? "All fields populated"
                  : "Some fields had errors"}
              </p>
              <p className="text-xs text-gray-500">
                {result.filled_fields}/{result.total_fields} fields &middot;{" "}
                {result.errors.length} errors
              </p>
            </div>
          </div>

          {result.errors.length > 0 && (
            <ul className="text-xs text-red-600 space-y-1 mb-4 pl-1">
              {result.errors.map((e, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-red-300 mt-0.5">&#x2022;</span>
                  {e}
                </li>
              ))}
            </ul>
          )}

          {result.screenshot_id && (
            <div className="mt-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
                <Image size={16} />
                Filled Form Preview
              </div>
              <img
                src={screenshotUrl(result.screenshot_id)}
                alt="Filled form screenshot"
                className="w-full rounded-xl border border-gray-200 shadow-lg"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
