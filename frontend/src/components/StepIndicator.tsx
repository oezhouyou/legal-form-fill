import { Check, Upload, FileSearch, Play } from "lucide-react";

const steps = [
  { label: "Upload", icon: Upload },
  { label: "Review", icon: FileSearch },
  { label: "Fill Form", icon: Play },
];

export default function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {steps.map((step, i) => {
        const done = i < current;
        const active = i === current;
        const Icon = done ? Check : step.icon;

        return (
          <div key={step.label} className="flex items-center gap-2">
            {i > 0 && (
              <div
                className={`h-0.5 w-12 ${done ? "bg-blue-600" : "bg-gray-300"}`}
              />
            )}
            <div className="flex flex-col items-center gap-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                  done
                    ? "bg-blue-600 text-white"
                    : active
                      ? "bg-blue-100 text-blue-700 ring-2 ring-blue-600"
                      : "bg-gray-100 text-gray-400"
                }`}
              >
                <Icon size={18} />
              </div>
              <span
                className={`text-xs font-medium ${active ? "text-blue-700" : done ? "text-blue-600" : "text-gray-400"}`}
              >
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
