import type {
  ExtractionResult,
  FormData,
  FormFillProgress,
  FormFillResult,
  UploadResult,
} from "./types";

const BASE = "";

export async function uploadFile(
  file: File,
  docType: string = "auto"
): Promise<UploadResult> {
  const form = new window.FormData();
  form.append("file", file);
  form.append("doc_type", docType);

  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function extractData(
  files: Record<string, string>
): Promise<ExtractionResult> {
  const res = await fetch(`${BASE}/api/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ files }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fillForm(data: FormData): Promise<FormFillResult> {
  const res = await fetch(`${BASE}/api/fill-form`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function connectProgress(
  onMessage: (msg: FormFillProgress) => void
): WebSocket {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${proto}//${window.location.host}/ws/progress`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
}

export function screenshotUrl(id: string): string {
  return `${BASE}/api/screenshots/${id}`;
}

export interface HealthStatus {
  status: string;
  checks: {
    anthropic_api_key: string;
    upload_directory: string;
  };
}

export async function checkHealth(): Promise<HealthStatus> {
  const res = await fetch(`${BASE}/api/health`);
  return res.json();
}
