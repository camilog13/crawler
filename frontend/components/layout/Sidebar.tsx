"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Globe2 } from "lucide-react";

const navItems = [{ href: "/projects", label: "Proyectos", icon: Globe2 }];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-seoCard border-r border-slate-800 flex flex-col">
      <div className="px-4 py-5 border-b border-slate-800 flex items-center gap-2">
        <BarChart3 className="text-seoAccent" />
        <span className="font-semibold">SEO Auditor</span>
      </div>

      <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition ${
                active ? "bg-seoAccentSoft text-white" : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
