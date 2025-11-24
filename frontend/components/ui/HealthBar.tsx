export default function HealthBar({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(100, value));

  const color =
    clamped >= 85
      ? "from-emerald-400 to-emerald-600"
      : clamped >= 60
      ? "from-yellow-400 to-yellow-600"
      : "from-red-400 to-red-600";

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-slate-400">
        <span>Site Health</span>
        <span className="font-semibold text-slate-100">
          {clamped.toFixed(1)}%
        </span>
      </div>
      <div className="h-3 w-full rounded-full bg-slate-800 overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${color} transition-all`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
