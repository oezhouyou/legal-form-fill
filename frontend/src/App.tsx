import { useState, useCallback, useRef, useEffect } from "react";
import {
  Scale,
  ArrowRight,
  ArrowLeft,
  Loader2,
  RotateCcw,
  Sparkles,
  Zap,
  AlertTriangle,
} from "lucide-react";

import StepIndicator from "./components/StepIndicator";
import FileUpload from "./components/FileUpload";
import ExtractedData from "./components/ExtractedData";
import ProgressView from "./components/ProgressView";

import { extractData, fillForm, connectProgress, checkHealth } from "./api";
import type { HealthStatus } from "./api";
import type {
  UploadResult,
  FormData,
  ExtractionResult,
  FormFillProgress,
  FormFillResult,
} from "./types";

const EMPTY_FORM: FormData = {
  attorney: {
    online_account: null,
    family_name: "",
    given_name: "",
    middle_name: null,
    street_number: "",
    apt_type: null,
    apt_number: null,
    city: "",
    state: "",
    zip_code: "",
    country: "United States",
    daytime_phone: "",
    mobile_phone: null,
    email: null,
  },
  eligibility: {
    is_attorney: false,
    licensing_authority: null,
    bar_number: null,
    subject_to_orders: null,
    law_firm: null,
    is_accredited_rep: false,
    recognized_org: null,
    accreditation_date: null,
    is_associated: false,
    associated_with_name: null,
    is_law_student: false,
    student_name: null,
  },
  passport: {
    surname: "",
    given_names: "",
    middle_names: null,
    passport_number: "",
    country_of_issue: "",
    nationality: "",
    date_of_birth: "",
    place_of_birth: "",
    sex: null,
    issue_date: "",
    expiry_date: "",
  },
};

export default function App() {
  const [step, setStep] = useState(0);
  const [healthIssues, setHealthIssues] = useState<string[]>([]);
  const [backendReady, setBackendReady] = useState(true);

  const [passportFile, setPassportFile] = useState<UploadResult | null>(null);
  const [g28File, setG28File] = useState<UploadResult | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [warnings, setWarnings] = useState<string[]>([]);

  const [filling, setFilling] = useState(false);
  const [progressItems, setProgressItems] = useState<FormFillProgress[]>([]);
  const [fillResult, setFillResult] = useState<FormFillResult | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    return () => wsRef.current?.close();
  }, []);

  useEffect(() => {
    checkHealth()
      .then((h: HealthStatus) => {
        const issues: string[] = [];
        if (h.checks.anthropic_api_key === "missing")
          issues.push("Anthropic API key is not configured — document extraction will not work.");
        if (h.checks.anthropic_api_key === "invalid")
          issues.push("Anthropic API key is invalid — document extraction will not work.");
        if (h.checks.upload_directory === "unavailable")
          issues.push("Upload directory is not writable — file uploads will fail.");
        setHealthIssues(issues);
        setBackendReady(h.status === "ok");
      })
      .catch(() => {
        setHealthIssues(["Unable to reach the backend server."]);
        setBackendReady(false);
      });
  }, []);

  const handleExtract = useCallback(async () => {
    const files: Record<string, string> = {};
    if (passportFile) files[passportFile.file_id] = passportFile.doc_type;
    if (g28File) files[g28File.file_id] = g28File.doc_type;

    setExtracting(true);
    setExtractError(null);

    try {
      const result: ExtractionResult = await extractData(files);
      setFormData(result.data);
      setWarnings(result.warnings);
      setStep(1);
    } catch (e: unknown) {
      setExtractError(e instanceof Error ? e.message : "Extraction failed");
    } finally {
      setExtracting(false);
    }
  }, [passportFile, g28File]);

  const handleFill = useCallback(async () => {
    setFilling(true);
    setProgressItems([]);
    setFillResult(null);

    const ws = connectProgress((msg) => {
      setProgressItems((prev) => [...prev, msg]);
    });
    wsRef.current = ws;

    try {
      const result = await fillForm(formData);
      setFillResult(result);
    } catch (e: unknown) {
      setFillResult({
        success: false,
        screenshot_id: null,
        filled_fields: 0,
        total_fields: 0,
        errors: [e instanceof Error ? e.message : "Form fill failed"],
      });
    } finally {
      setFilling(false);
      ws.close();
    }
  }, [formData]);

  const reset = () => {
    setStep(0);
    setPassportFile(null);
    setG28File(null);
    setFormData(EMPTY_FORM);
    setWarnings([]);
    setProgressItems([]);
    setFillResult(null);
    setExtractError(null);
  };

  const hasFiles = passportFile !== null || g28File !== null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-4">
          <div className="w-11 h-11 bg-gradient-to-br from-brand-600 to-brand-800 rounded-xl flex items-center justify-center shadow-lg shadow-brand-600/20">
            <Scale className="text-white" size={21} />
          </div>
          <div className="flex-1">
            <h1 className="text-lg font-bold text-gray-900 tracking-tight">
              Legal Form Fill
            </h1>
            <p className="text-xs text-gray-400 font-medium">
              AI-Powered Document Extraction & Automation
            </p>
          </div>
          <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-gray-400 font-medium bg-gray-50 px-3 py-1.5 rounded-full">
            <Zap size={12} className="text-amber-400" />
            Powered by Claude Vision + Playwright
          </div>
        </div>
      </header>

      {healthIssues.length > 0 && (
        <div className="max-w-5xl mx-auto px-6 pt-6">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 animate-fade-in">
            <AlertTriangle size={18} className="text-amber-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              {healthIssues.map((msg, i) => (
                <p key={i} className="text-sm text-amber-700">{msg}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      <main className="max-w-5xl mx-auto px-6 py-10">
        <StepIndicator current={step} />

        {/* Step 0: Upload */}
        {step === 0 && (
          <div className="animate-fade-in space-y-6">
            <div className="bg-white rounded-2xl shadow-sm shadow-gray-200/50 border border-gray-100 p-8">
              <div className="text-center mb-8">
                <h2 className="text-xl font-bold text-gray-900">
                  Upload Your Documents
                </h2>
                <p className="text-sm text-gray-500 mt-2 max-w-md mx-auto">
                  Upload a passport and/or G-28 form. Our AI will extract
                  structured data from your documents automatically.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <FileUpload
                  label="Passport"
                  description="Photo page — PDF, JPG or PNG"
                  docType="passport"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onUploaded={setPassportFile}
                />
                <FileUpload
                  label="G-28 Form"
                  description="Notice of Appearance — PDF"
                  docType="g28"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onUploaded={setG28File}
                />
              </div>

              {extractError && (
                <div className="mt-6 bg-red-50 border border-red-100 rounded-xl p-4 text-sm text-red-700 animate-fade-in">
                  {extractError}
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <button
                disabled={!hasFiles || extracting || !backendReady}
                onClick={handleExtract}
                className="group flex items-center gap-2.5 px-7 py-3.5 bg-brand-600 text-white rounded-xl font-semibold text-sm hover:bg-brand-700 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-brand-600/20 hover:shadow-xl hover:shadow-brand-600/25"
              >
                {extracting ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Analyzing Documents...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Extract Data
                    <ArrowRight
                      size={16}
                      className="group-hover:translate-x-0.5 transition-transform"
                    />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 1: Review */}
        {step === 1 && (
          <div className="animate-fade-in space-y-6">
            <div className="bg-white rounded-2xl shadow-sm shadow-gray-200/50 border border-gray-100 p-8">
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Review Extracted Data
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                  Verify and correct the information below before populating
                  the form.
                </p>
              </div>

              <ExtractedData
                data={formData}
                warnings={warnings}
                onChange={setFormData}
              />
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep(0)}
                className="flex items-center gap-2 px-5 py-3 border border-gray-200 text-gray-600 rounded-xl font-medium text-sm hover:bg-gray-50 active:scale-[0.98] transition-all"
              >
                <ArrowLeft size={16} />
                Back
              </button>
              <button
                disabled={filling}
                onClick={() => {
                  setStep(2);
                  handleFill();
                }}
                className="group flex items-center gap-2.5 px-7 py-3.5 bg-brand-600 text-white rounded-xl font-semibold text-sm hover:bg-brand-700 active:scale-[0.98] disabled:opacity-40 transition-all shadow-lg shadow-brand-600/20 hover:shadow-xl hover:shadow-brand-600/25"
              >
                <Sparkles size={18} />
                Fill Form
                <ArrowRight
                  size={16}
                  className="group-hover:translate-x-0.5 transition-transform"
                />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Fill */}
        {step === 2 && (
          <div className="animate-fade-in space-y-6">
            <div className="bg-white rounded-2xl shadow-sm shadow-gray-200/50 border border-gray-100 p-8">
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Automated Form Filling
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                  Playwright is populating each field on the target form
                  in real time.
                </p>
              </div>

              <ProgressView items={progressItems} result={fillResult} />
            </div>

            {fillResult && (
              <div className="flex justify-center">
                <button
                  onClick={reset}
                  className="flex items-center gap-2 px-6 py-3 border border-gray-200 text-gray-600 rounded-xl font-medium text-sm hover:bg-gray-50 active:scale-[0.98] transition-all"
                >
                  <RotateCcw size={16} />
                  Start Over
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="text-center text-[11px] text-gray-300 py-8 font-medium">
        FastAPI &middot; Claude Vision &middot; Playwright &middot; React &middot; Tailwind
      </footer>
    </div>
  );
}
