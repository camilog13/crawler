"use client";

import { useState } from "react";
import type { Issue, IssueDetailsPayload } from "@/lib/types";
import Toggle from "@/components/ui/Toggle";
import { updateIssue } from "@/lib/api";

interface Props {
  issues: Issue[];
}

export default function IssueTable({ issues: initialIssues }: Props) {
  const [rows, setRows] = useState<Issue[]>(initialIssues);
  const [savingId, setSavingId] = useState<number | null>(null);

  const parseDetails = (issue: Issue): IssueDetailsPayload => {
    try {
      return JSON.parse(issue.details || "{}");
    } catch {
      return {} as IssueDetailsPayload;
    }
  };

  const handleToggleImplemented = async (issue: Issue, value: boolean) => {
    setSavingId(issue.id);
    try {
      const updated = await updateIssue(issue.id, { implemented: value });
      setRows((prev) => prev.map((r) => (r.id === issue.id ? updated : r)));
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="overflow-auto scrollbar-thin">
      <table className="min-w-full text-xs">
        <thead className="bg-slate-900/60">
          <tr>
            <th className="px-3 py-2 text-left font-medium text-slate-400 w-[32%]">
              URL
            </th>
            <th className="px-3 py-2 text-left font-medium text-slate-400">
              Estado / Métricas
            </th>
            <th className="px-3 py-2 text-left font-medium text-slate-400 w-[32%]">
              Explicación e instrucción
            </th>
            <th className="px-3 py-2 text-center font-medium text-slate-400">
              Implementado
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map((issue) => {
            const d = parseDetails(issue);
            const status =
              typeof (d as any).status_code === "number"
                ? (d as any).status_code
                : null;

            const perf: string[] = [];
            if ((d as any).lcp_ms) perf.push(`LCP: ${(d as any).lcp_ms.toFixed(0)} ms`);
            if ((d as any).cls) perf.push(`CLS: ${(d as any).cls.toFixed(3)}`);
            if ((d as any).tbt_ms)
              perf.push(`TBT: ${(d as any).tbt_ms.toFixed(0)} ms`);
            if ((d as any).performance_score_mobile)
              perf.push(
                `Score mobile: ${(d as any).performance_score_mobile.toFixed(0)}`
              );

            const hint =
              d.hint || "Aplica el ajuste recomendado para este tipo de issue.";

            const extraKeys = Object.keys(d).filter(
              (k) =>
                ![
                  "url",
                  "issue_code",
                  "issue_name",
                  "severity",
                  "category",
                  "hint"
                ].includes(k)
            );

            return (
              <tr key={issue.id} className="hover:bg-slate-900/40 align-top">
                <td className="px-3 py-2">
                  <a
                    href={d.url || "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] text-seoAccent hover:underline break-all"
                  >
                    {d.url || "URL no disponible"}
                  </a>
                  {status !== null && (
                    <div className="mt-1 text-[11px] text-slate-500">
                      HTTP {status}
                    </div>
                  )}
                </td>

                <td className="px-3 py-2 text-[11px] text-slate-300 space-y-1">
                  {perf.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {perf.map((p) => (
                        <span
                          key={p}
                          className="bg-slate-800/80 rounded-full px-2 py-0.5"
                        >
                          {p}
                        </span>
                      ))}
                    </div>
                  )}

                  {extraKeys.length > 0 && (
                    <div className="mt-1 space-y-0.5 text-slate-400">
                      {extraKeys.map((k) => (
                        <div key={k}>
                          <span className="text-slate-500">{k}</span>
                          <span className="mx-1 text-slate-600">=</span>
                          <span className="font-mono">
                            {String((d as any)[k])}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </td>

                <td className="px-3 py-2 text-[11px] text-slate-300">
                  <div className="font-semibold mb-1 text-slate-100">
                    Qué está pasando
                  </div>
                  <p className="text-slate-300">
                    {d.issue_name || `Issue ${issue.id}`}
                  </p>

                  <div className="font-semibold mt-2 mb-1 text-slate-100">
                    Qué debe hacer el implementador
                  </div>
                  <p className="text-slate-300">{hint}</p>

                  {issue.comment && (
                    <p className="mt-2 text-[11px] text-slate-400">
                      <span className="font-semibold text-slate-300">
                        Nota interna
                      </span>{" "}
                      {issue.comment}
                    </p>
                  )}
                </td>

                <td className="px-3 py-2 text-center">
                  <div className="flex flex-col items-center gap-1">
                    <Toggle
                      checked={issue.implemented}
                      onChange={(v) => handleToggleImplemented(issue, v)}
                    />
                    <span
                      className={`text-[10px] ${
                        issue.implemented ? "text-emerald-300" : "text-slate-500"
                      }`}
                    >
                      {issue.implemented ? "Aplicado" : "Pendiente"}
                    </span>
                    {savingId === issue.id && (
                      <span className="text-[10px] text-slate-400">
                        Guardando...
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}

          {rows.length === 0 && (
            <tr>
              <td
                colSpan={4}
                className="px-3 py-4 text-center text-slate-500 text-xs"
              >
                No hay URLs afectadas para este issue en el crawl actual.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
