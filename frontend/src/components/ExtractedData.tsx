import { useState } from "react";
import {
  AlertTriangle,
  User,
  Scale,
  BookOpen,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import type { FormData } from "../types";

interface Props {
  data: FormData;
  warnings: string[];
  onChange: (data: FormData) => void;
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const filled = value.trim().length > 0;

  return (
    <div className="group">
      <label className="block text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full px-3.5 py-2.5 rounded-xl text-sm transition-all duration-200 outline-none border ${
          filled
            ? "border-gray-200 bg-white text-gray-900 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20"
            : "border-dashed border-gray-200 bg-gray-50/50 text-gray-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 focus:bg-white"
        }`}
        placeholder="—"
      />
    </div>
  );
}

function Section({
  title,
  icon: Icon,
  defaultOpen = true,
  children,
}: {
  title: string;
  icon: React.ElementType;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-xl border border-gray-100 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-5 py-3.5 bg-gray-50/70 hover:bg-gray-50 transition-colors text-left"
      >
        <div className="w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center shadow-sm">
          <Icon size={15} className="text-brand-600" />
        </div>
        <span className="text-sm font-semibold text-gray-800 flex-1">
          {title}
        </span>
        {open ? (
          <ChevronDown size={16} className="text-gray-400" />
        ) : (
          <ChevronRight size={16} className="text-gray-400" />
        )}
      </button>
      {open && (
        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in">
          {children}
        </div>
      )}
    </div>
  );
}

export default function ExtractedData({ data, warnings, onChange }: Props) {
  const updateAttorney = (field: string, value: string) => {
    onChange({ ...data, attorney: { ...data.attorney, [field]: value } });
  };
  const updateEligibility = (field: string, value: string) => {
    onChange({ ...data, eligibility: { ...data.eligibility, [field]: value } });
  };
  const updatePassport = (field: string, value: string) => {
    onChange({ ...data, passport: { ...data.passport, [field]: value } });
  };

  return (
    <div className="space-y-4">
      {warnings.length > 0 && (
        <div className="animate-fade-in rounded-xl bg-amber-50 border border-amber-200/60 p-4">
          <div className="flex items-center gap-2 text-amber-700 font-semibold text-sm mb-2">
            <AlertTriangle size={16} />
            Extraction Warnings
          </div>
          <ul className="space-y-1">
            {warnings.map((w, i) => (
              <li
                key={i}
                className="text-xs text-amber-600/90 pl-6 relative before:content-[''] before:absolute before:left-2 before:top-[7px] before:w-1.5 before:h-1.5 before:rounded-full before:bg-amber-300"
              >
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Section title="Attorney / Representative" icon={User}>
        <Field label="Family Name" value={data.attorney.family_name} onChange={(v) => updateAttorney("family_name", v)} />
        <Field label="Given Name" value={data.attorney.given_name} onChange={(v) => updateAttorney("given_name", v)} />
        <Field label="Middle Name" value={data.attorney.middle_name ?? ""} onChange={(v) => updateAttorney("middle_name", v)} />
        <Field label="Street Address" value={data.attorney.street_number} onChange={(v) => updateAttorney("street_number", v)} />
        <Field label="City" value={data.attorney.city} onChange={(v) => updateAttorney("city", v)} />
        <Field label="State" value={data.attorney.state} onChange={(v) => updateAttorney("state", v)} />
        <Field label="ZIP Code" value={data.attorney.zip_code} onChange={(v) => updateAttorney("zip_code", v)} />
        <Field label="Country" value={data.attorney.country} onChange={(v) => updateAttorney("country", v)} />
        <Field label="Daytime Phone" value={data.attorney.daytime_phone} onChange={(v) => updateAttorney("daytime_phone", v)} />
        <Field label="Mobile Phone" value={data.attorney.mobile_phone ?? ""} onChange={(v) => updateAttorney("mobile_phone", v)} />
        <Field label="Email" value={data.attorney.email ?? ""} onChange={(v) => updateAttorney("email", v)} />
      </Section>

      <Section title="Eligibility Information" icon={Scale}>
        <Field label="Licensing Authority" value={data.eligibility.licensing_authority ?? ""} onChange={(v) => updateEligibility("licensing_authority", v)} />
        <Field label="Bar Number" value={data.eligibility.bar_number ?? ""} onChange={(v) => updateEligibility("bar_number", v)} />
        <Field label="Law Firm / Organization" value={data.eligibility.law_firm ?? ""} onChange={(v) => updateEligibility("law_firm", v)} />
      </Section>

      <Section title="Passport / Beneficiary" icon={BookOpen}>
        <Field label="Surname" value={data.passport.surname} onChange={(v) => updatePassport("surname", v)} />
        <Field label="Given Names" value={data.passport.given_names} onChange={(v) => updatePassport("given_names", v)} />
        <Field label="Middle Names" value={data.passport.middle_names ?? ""} onChange={(v) => updatePassport("middle_names", v)} />
        <Field label="Passport Number" value={data.passport.passport_number} onChange={(v) => updatePassport("passport_number", v)} />
        <Field label="Country of Issue" value={data.passport.country_of_issue} onChange={(v) => updatePassport("country_of_issue", v)} />
        <Field label="Nationality" value={data.passport.nationality} onChange={(v) => updatePassport("nationality", v)} />
        <Field label="Date of Birth" value={data.passport.date_of_birth} onChange={(v) => updatePassport("date_of_birth", v)} />
        <Field label="Place of Birth" value={data.passport.place_of_birth} onChange={(v) => updatePassport("place_of_birth", v)} />
        <Field label="Sex" value={data.passport.sex ?? ""} onChange={(v) => updatePassport("sex", v)} />
        <Field label="Issue Date" value={data.passport.issue_date} onChange={(v) => updatePassport("issue_date", v)} />
        <Field label="Expiry Date" value={data.passport.expiry_date} onChange={(v) => updatePassport("expiry_date", v)} />
      </Section>
    </div>
  );
}
