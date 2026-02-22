import { useState, useCallback, useRef, useEffect } from "react";
import {
  FileText,
  ArrowRight,
  ArrowLeft,
  Loader2,
  RotateCcw,
} from "lucide-react";

import StepIndicator from "./components/StepIndicator";
import FileUpload from "./components/FileUpload";
import ExtractedData from "./components/ExtractedData";
import ProgressView from "./components/ProgressView";

import { extractData, fillForm, connectProgress } from "./api";
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

  // Step 0: Upload
  const [passportFile, setPassportFile] = useState<UploadResult | null>(null);
  const [g28File, setG28File] = useState<UploadResult | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  // Step 1: Review
  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [warnings, setWarnings] = useState<string[]>([]);

  // Step 2: Fill
  const [filling, setFilling] = useState(false);
  const [progressItems, setProgressItems] = useState<FormFillProgress[]>([]);
  const [fillResult, setFillResult] = useState<FormFillResult | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Cleanup WS on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
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

    // Connect WebSocket for progress
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <FileText className="text-white" size={22} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">Legal Form Fill</h1>
            <p className="text-xs text-gray-500">
              Automated document extraction & form population
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <StepIndicator current={step} />

        {/* Step 0: Upload */}
        {step === 0 && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">
                Upload Documents
              </h2>
              <p className="text-sm text-gray-500 mb-6">
                Upload a passport and/or G-28 form. The system will extract data
                using AI-powered vision analysis.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FileUpload
                  label="Passport Image"
                  docType="passport"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onUploaded={setPassportFile}
                />
                <FileUpload
                  label="G-28 Form (PDF)"
                  docType="g28"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onUploaded={setG28File}
                />
              </div>

              {extractError && (
                <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                  {extractError}
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <button
                disabled={!hasFiles || extracting}
                onClick={handleExtract}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {extracting ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    Extracting Data...
                  </>
                ) : (
                  <>
                    Extract & Continue
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 1: Review */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-1">
                Review Extracted Data
              </h2>
              <p className="text-sm text-gray-500 mb-6">
                Verify and correct the extracted information before filling the
                form.
              </p>

              <ExtractedData
                data={formData}
                warnings={warnings}
                onChange={setFormData}
              />
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep(0)}
                className="flex items-center gap-2 px-5 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                <ArrowLeft size={18} />
                Back
              </button>
              <button
                disabled={filling}
                onClick={() => {
                  setStep(2);
                  handleFill();
                }}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                Fill Form
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Fill */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-1">
                Automated Form Filling
              </h2>
              <p className="text-sm text-gray-500 mb-6">
                Playwright is navigating to the form and filling in each field.
              </p>

              <ProgressView items={progressItems} result={fillResult} />
            </div>

            <div className="flex justify-center">
              {fillResult && (
                <button
                  onClick={reset}
                  className="flex items-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  <RotateCcw size={18} />
                  Start Over
                </button>
              )}
            </div>
          </div>
        )}
      </main>

      <footer className="text-center text-xs text-gray-400 py-6">
        Built with FastAPI + Claude Vision + Playwright + React
      </footer>
    </div>
  );
}
