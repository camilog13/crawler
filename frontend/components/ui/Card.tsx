import type { ReactNode } from "react";
import clsx from "clsx";

export default function Card({
  children,
  className
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "bg-seoCard border border-slate-800 rounded-xl p-4 shadow-md shadow-black/40",
        className
      )}
    >
      {children}
    </div>
  );
}
