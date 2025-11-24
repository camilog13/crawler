"use client";

import { ReactNode, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

const AUTH_KEY = "seo-auditor-auth";

export default function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (pathname === "/login") {
      setAuthorized(true);
      return;
    }

    const ok = localStorage.getItem(AUTH_KEY) === "ok";
    if (!ok) {
      router.replace("/login");
    } else {
      setAuthorized(true);
    }
  }, [pathname, router]);

  if (!authorized) return null;

  return <>{children}</>;
}
