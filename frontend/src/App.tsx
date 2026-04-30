import { useEffect, useState } from "react";
import { getStats, syncLeads } from "./api";
import { Activity, RefreshCw } from "lucide-react"; // Додано RefreshCw
import LeadsTable from "./components/LeadsTable";

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
  const [isSyncing, setIsSyncing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0); // Ключ для примусового рендеру таблиці

  const fetchStats = () => {
    getStats()
      .then((data) => {
        setStats(data);
        setError(null);
      })
      .catch((err) => {
        console.error("API Error:", err);
        setError(err.message || "Помилка підключення до API");
      });
  };

  useEffect(() => {
    fetchStats();
  }, [refreshKey]); // Оновлюємо статистику при зміні ключа

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      await syncLeads();
      setRefreshKey((prev) => prev + 1); // Тригер оновлення таблиці і статистики
    } catch (err) {
      console.error("Sync failed:", err);
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      alert("Помилка синхронізації: " + errorMessage);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-blue-500" />
            <h1 className="text-3xl font-bold">FastGram Dashboard</h1>
          </div>

          {/* Кнопка синхронізації */}
          <button
            onClick={handleSync}
            disabled={isSyncing}
            className={`flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium ${isSyncing ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            <RefreshCw
              className={`w-5 h-5 ${isSyncing ? "animate-spin" : ""}`}
            />
            {isSyncing ? "Синхронізація..." : "Синхронізувати з Sheets"}
          </button>
        </div>

        {error ? (
          <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-lg">
            Критична помилка: {error}. Перевір F12 -&gt; Network.
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

        {/* Передаємо refreshKey, щоб таблиця оновлювалась після синку */}
        {!error && <LeadsTable key={refreshKey} />}
      </div>
    </div>
  );
}

export default App;
