"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { CrawlSummary } from "@/lib/types";

export default function IssuesBySeverityChart({ summary }: { summary: CrawlSummary }) {
  const data = Object.entries(summary.issues_by_severity || {}).map(([k, v]) => ({
    severity: k,
    count: v
  }));

  const labelMap: Record<string, string> = {
    critical: "Críticos",
    major: "Importantes",
    minor: "Menores"
  };

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis
            dataKey="severity"
            tickFormatter={(s) => labelMap[s] || s}
            stroke="#94a3b8"
          />
          <YAxis stroke="#94a3b8" />
          <Tooltip
            contentStyle={{ background: "#020617", border: "1px solid #1e293b" }}
            labelFormatter={(s) => labelMap[s as string] || s}
          />
          <Bar dataKey="count" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
