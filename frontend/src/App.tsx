import { StrictMode } from "react";

export default function App() {
  return (
    <StrictMode>
      <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">
        <div className="animate-pulse flex items-center gap-2 text-xl">
          Ініціалізація архітектури (Phase 1)...
        </div>
      </div>
    </StrictMode>
  );
}
