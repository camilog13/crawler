import "./globals.css";
import type { ReactNode } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";

export const metadata = {
  title: "SEO Auditor",
  description: "Auditoría SEO visual estilo Semrush"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body className="bg-seoBg text-slate-100">
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex-1 flex flex-col">
            <Topbar />
            <main className="flex-1 overflow-auto p-6 scrollbar-thin">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
