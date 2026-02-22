import { Check, Loader2, AlertCircle, Image } from "lucide-react";
import type { FormFillProgress, FormFillResult } from "../types";
import { screenshotUrl } from "../api";

interface Props {
  items: FormFillProgress[];
  result: FormFillResult | null;
}

export default function ProgressView({ items, result }: Props) {
  const latestProgress = items.length > 0 ? items[items.length - 1].progress : 0;

  return (
    <div className="space-y-6">
      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span className="font-medium text-gray-700">
            {result ? "Completed" : "Filling form..."}
          </span>
          <span className="text-gray-500">{Math.round(latestProgress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${latestProgress}%` }}
          />
        </div>
      </div>

      {/* Field log */}
      <div className="max-h-64 overflow-y-auto border rounded-lg divide-y">
        {items.map((item, i) => (
          <div
            key={i}
            className="flex items-center gap-2 px-3 py-2 text-sm"
          >
            {item.status === "filling" && (
              <Loader2 size={14} className="text-blue-500 animate-spin shrink-0" />
            )}
            {item.status === "done" && (
              <Check size={14} className="text-green-500 shrink-0" />
            )}
            {item.status === "error" && (
              <AlertCircle size={14} className="text-red-500 shrink-0" />
            )}
            <span className="font-mono text-xs text-gray-600 truncate">
              {item.field}
            </span>
            <span className="ml-auto text-xs text-gray-400 truncate max-w-48">
              {item.message}
            </span>
          </div>
        ))}
      </div>

      {/* Result */}
      {result && (
        <div
          className={`rounded-lg p-4 ${result.success ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}
        >
          <p
            className={`font-semibold ${result.success ? "text-green-800" : "text-red-800"}`}
          >
            {result.success ? "Form filled successfully!" : "Form filling completed with errors"}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            {result.filled_fields} of {result.total_fields} fields filled
          </p>
          {result.errors.length > 0 && (
            <ul className="text-xs text-red-600 mt-2 list-disc list-inside">
              {result.errors.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          )}

          {result.screenshot_id && (
            <div className="mt-4">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Image size={16} />
                Filled Form Screenshot
              </div>
              <img
                src={screenshotUrl(result.screenshot_id)}
                alt="Filled form screenshot"
                className="w-full rounded-lg border shadow-sm"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
