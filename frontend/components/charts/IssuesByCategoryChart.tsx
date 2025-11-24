"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import type { CrawlSummary } from "@/lib/types";

const COLORS = ["#3b82f6", "#22c55e", "#f97316", "#eab308", "#ec4899", "#8b5cf6"];

export default function IssuesByCategoryChart({ summary }: { summary: CrawlSummary }) {
  const data = Object.entries(summary.issues_by_category || {}).map(([k, v]) => ({
    category: k,
    value: v
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            dataKey="value"
            data={data}
            outerRadius={90}
            innerRadius={50}
            isAnimationActive
            paddingAngle={4}
          >
            {data.map((entry, index) => (
              <Cell key={entry.category} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#020617", border: "1px solid #1e293b" }}
            formatter={(v) => [`${v} issues`, "Cantidad"]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
