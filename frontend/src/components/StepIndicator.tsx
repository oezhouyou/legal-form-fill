import { Check, CloudUpload, ScanSearch, Sparkles } from "lucide-react";

const steps = [
  { label: "Upload", desc: "Add documents", icon: CloudUpload },
  { label: "Review", desc: "Verify data", icon: ScanSearch },
  { label: "Auto-Fill", desc: "Populate form", icon: Sparkles },
];

export default function StepIndicator({ current }: { current: number }) {
  return (
    <nav className="mb-10">
      <ol className="flex items-center justify-center">
        {steps.map((step, i) => {
          const done = i < current;
          const active = i === current;
          const Icon = done ? Check : step.icon;

          return (
            <li key={step.label} className="flex items-center">
              {i > 0 && (
                <div
                  className={`w-16 sm:w-24 h-px mx-1 transition-colors duration-500 ${
                    done ? "bg-brand-600" : "bg-gray-200"
                  }`}
                />
              )}
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={`relative w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-300 ${
                    done
                      ? "bg-brand-600 text-white shadow-md shadow-brand-600/25"
                      : active
                        ? "bg-brand-50 text-brand-700 ring-2 ring-brand-500 shadow-sm"
                        : "bg-gray-100 text-gray-400"
                  }`}
                >
                  <Icon size={19} strokeWidth={done ? 2.5 : 2} />
                  {active && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-brand-500 rounded-full animate-pulse-soft" />
                  )}
                </div>
                <div className="text-center">
                  <p
                    className={`text-xs font-semibold leading-none ${
                      active ? "text-brand-700" : done ? "text-brand-600" : "text-gray-400"
                    }`}
                  >
                    {step.label}
                  </p>
                  <p className="text-[10px] text-gray-400 mt-0.5 hidden sm:block">
                    {step.desc}
                  </p>
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
