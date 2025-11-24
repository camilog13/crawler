const mapCat: Record<string, string> = {
  technical: "bg-sky-500/10 text-sky-300 border-sky-500/40",
  content: "bg-emerald-500/10 text-emerald-300 border-emerald-500/40",
  links: "bg-purple-500/10 text-purple-300 border-purple-500/40",
  performance: "bg-pink-500/10 text-pink-300 border-pink-500/40",
  sitemap: "bg-amber-500/10 text-amber-200 border-amber-500/40",
  structured_data: "bg-indigo-500/10 text-indigo-300 border-indigo-500/40",
  security: "bg-rose-500/10 text-rose-300 border-rose-500/40",
  internationalization: "bg-fuchsia-500/10 text-fuchsia-300 border-fuchsia-500/40",
  javascript: "bg-lime-500/10 text-lime-300 border-lime-500/40"
};

export default function CategoryPill({ category }: { category: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wide ${
        mapCat[category] || "bg-slate-700 text-slate-200 border-slate-500"
      }`}
    >
      {category}
    </span>
  );
}
