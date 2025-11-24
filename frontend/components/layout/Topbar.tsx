"use client";

import { Github, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

const AUTH_KEY = "seo-auditor-auth";

export default function Topbar() {
  const router = useRouter();

  const logout = () => {
    localStorage.removeItem(AUTH_KEY);
    router.replace("/login");
  };

  return (
    <header className="h-14 border-b border-slate-800 flex items-center justify-between px-6 bg-seoCard">
      <div className="text-sm text-slate-400">Dashboard de auditorías SEO</div>

      <div className="flex items-center gap-3">
        <a
          href="https://github.com/camilog13/crawler"
          target="_blank"
          rel="noreferrer"
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
        >
          <Github size={16} /> Repo
        </a>

        <button
          onClick={logout}
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
        >
          <LogOut size={16} /> Salir
        </button>
      </div>
    </header>
  );
}
