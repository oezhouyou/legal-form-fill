export interface AttorneyInfo {
  online_account: string | null;
  family_name: string;
  given_name: string;
  middle_name: string | null;
  street_number: string;
  apt_type: "apt" | "ste" | "flr" | null;
  apt_number: string | null;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  daytime_phone: string;
  mobile_phone: string | null;
  email: string | null;
}

export interface EligibilityInfo {
  is_attorney: boolean;
  licensing_authority: string | null;
  bar_number: string | null;
  subject_to_orders: "not" | "am" | null;
  law_firm: string | null;
  is_accredited_rep: boolean;
  recognized_org: string | null;
  accreditation_date: string | null;
  is_associated: boolean;
  associated_with_name: string | null;
  is_law_student: boolean;
  student_name: string | null;
}

export interface PassportInfo {
  surname: string;
  given_names: string;
  middle_names: string | null;
  passport_number: string;
  country_of_issue: string;
  nationality: string;
  date_of_birth: string;
  place_of_birth: string;
  sex: "M" | "F" | "X" | null;
  issue_date: string;
  expiry_date: string;
}

export interface FormData {
  attorney: AttorneyInfo;
  eligibility: EligibilityInfo;
  passport: PassportInfo;
}

export interface ExtractionResult {
  data: FormData;
  confidence: Record<string, number>;
  warnings: string[];
}

export interface UploadResult {
  file_id: string;
  filename: string;
  doc_type: string;
  preview_url: string;
}

export interface FormFillProgress {
  field: string;
  status: "filling" | "done" | "error";
  message: string;
  progress: number;
}

export interface FormFillResult {
  success: boolean;
  screenshot_id: string | null;
  filled_fields: number;
  total_fields: number;
  errors: string[];
}
