import type { Severity } from "@/lib/types";

const mapSeverity: Record<Severity, string> = {
  critical: "bg-seoCritical/20 text-red-300 border-red-500/50",
  major: "bg-seoMajor/20 text-orange-300 border-orange-500/50",
  minor: "bg-seoMinor/20 text-yellow-200 border-yellow-500/50"
};

export default function SeverityPill({ severity }: { severity: Severity }) {
  const label =
    severity === "critical"
      ? "Crítico"
      : severity === "major"
      ? "Importante"
      : "Menor";

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${mapSeverity[severity]}`}
    >
      {label}
    </span>
  );
}
