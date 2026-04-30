import { useEffect, useState } from "react";
import { getStats } from "./api";
import { Activity } from "lucide-react";

// Сувора типізація
interface DashboardStats {
  pending: number;
  sent: number;
  failed: number;
  replied: number;
  total: number;
}

function App() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats()
      .then((data) => {
        setStats(data);
        setError(null);
      })
      .catch((err) => {
        console.error("API Error:", err);
        setError(err.message || "Помилка підключення до API");
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <Activity className="w-8 h-8 text-blue-500" />
          <h1 className="text-3xl font-bold">FastGram Dashboard</h1>
        </div>

        {error ? (
          <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-lg">
            Критична помилка: {error}. Перевір F12 -&gt; Network (CORS або
            відключений бекенд).
          </div>
        ) : stats ? (
          <div className="grid grid-cols-5 gap-4">
            {Object.entries(stats).map(([key, value]) => (
              <div
                key={key}
                className="bg-gray-800 p-6 rounded-lg border border-gray-700"
              >
                <div className="text-gray-400 text-sm uppercase tracking-wider mb-2">
                  {key}
                </div>
                <div className="text-3xl font-bold">{String(value)}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500 animate-pulse">З'єднання з API...</div>
        )}
      </div>
    </div>
  );
}

export default App;
