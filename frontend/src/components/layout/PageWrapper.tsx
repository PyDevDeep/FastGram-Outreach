

import type { ReactNode } from "react";

interface PageWrapperProps {
  title: string;
  children: ReactNode;
}

export function PageWrapper({ title, children }: PageWrapperProps) {
  return (
    <div className="p-8 max-w-7xl mx-auto w-full h-full flex flex-col">
      <h1 className="text-3xl font-bold mb-8 text-foreground">{title}</h1>
      <div className="flex-1 flex flex-col gap-6">{children}</div>
    </div>
  );
}
