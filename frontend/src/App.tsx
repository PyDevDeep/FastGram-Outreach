import { useEffect, useState } from "react";
import { getStats, syncLeads, checkAuthStatus, triggerLogin } from "./api";
import { Activity, RefreshCw, ShieldAlert, KeyRound } from "lucide-react";
import LeadsTable from "./components/LeadsTable";

interface DashboardStats {
  pending: number;
  sent: number;
  failed: number;
  replied: number;
  total: number;
}

export default function App() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Auth States
  const [isAuthValid, setIsAuthValid] = useState<boolean | null>(null);
  const [isChallenge, setIsChallenge] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const fetchStats = () => {
    getStats()
      .then((data) => {
        setStats(data);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || "Помилка підключення до API");
      });
  };
  useEffect(() => {
    // Переносимо логіку ВСЕРЕДИНУ useEffect
    const verifySession = async () => {
      try {
        const res = await checkAuthStatus();
        setIsAuthValid(res.is_valid);
        if (!res.is_valid) {
          setAuthError(res.message || "Сесія невалідна. Потрібен логін.");
        }
      } catch (err) {
        setIsAuthValid(false);
        setAuthError(
          err instanceof Error ? err.message : "Помилка зв'язку з бекендом.",
        );
      }
    };

    verifySession();
  }, []);

  useEffect(() => {
    if (isAuthValid) {
      fetchStats();
    }
  }, [isAuthValid, refreshKey]);

  const handleLogin = async () => {
    setAuthLoading(true);
    setAuthError(null);
    try {
      const res = await triggerLogin(
        verificationCode ? verificationCode : undefined,
      );

      if (res.status === "success") {
        setIsAuthValid(true);
        setIsChallenge(false);
        setVerificationCode("");
      } else if (res.status === "challenge_required") {
        setIsChallenge(true);
        setAuthError(
          "Instagram вимагає підтвердження. Введи код з SMS/Пошти/Додатка.",
        );
      }
    } catch (err) {
      const e = err as {
        response?: { data?: { detail?: string } };
        message?: string;
      };
      setAuthError(
        e.response?.data?.detail || e.message || "Помилка авторизації",
      );
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      await syncLeads();
      setRefreshKey((prev) => prev + 1);
    } catch (err) {
      const e = err as {
        response?: { data?: { detail?: string } };
        message?: string;
      };
      setAuthError(
        e.response?.data?.detail || e.message || "Помилка синхронізації:",
      );
    } finally {
      setAuthLoading(false);
    }
  };

  // --- ЕКРАН ЗАВАНТАЖЕННЯ ---
  if (isAuthValid === null) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">
        <div className="animate-pulse flex items-center gap-2 text-xl">
          <Activity className="w-6 h-6 text-blue-500" /> Перевірка сесії
          Instagram...
        </div>
      </div>
    );
  }

  // --- ЕКРАН АВТОРИЗАЦІЇ / 2FA ---
  if (isAuthValid === false) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <div className="bg-gray-800 border border-gray-700 p-8 rounded-xl w-full max-w-md shadow-2xl">
          <div className="flex justify-center mb-6">
            <ShieldAlert className="w-16 h-16 text-red-500" />
          </div>
          <h2 className="text-2xl font-bold text-white text-center mb-2">
            Сесія не активна
          </h2>
          <p className="text-gray-400 text-center mb-6 text-sm">
            FastGram не може відправляти повідомлення. Потрібна повторна
            авторизація в Instagram.
          </p>

          {authError && (
            <div className="bg-red-900/30 border border-red-800 text-red-300 p-3 rounded mb-6 text-sm">
              {authError}
            </div>
          )}

          {isChallenge && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Код верифікації (2FA)
              </label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="123456"
                  className="w-full bg-gray-900 border border-gray-600 rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}

          <button
            onClick={handleLogin}
            disabled={authLoading}
            className={`w-full py-3 rounded-lg font-bold transition-colors ${
              authLoading
                ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 text-white"
            }`}
          >
            {authLoading
              ? "Обробка..."
              : isChallenge
                ? "Відправити код"
                : "Ініціювати Логін"}
          </button>
        </div>
      </div>
    );
  }

  // --- ЕКРАН ДАШБОРДУ (якщо isAuthValid === true) ---
  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-blue-500" />
            <h1 className="text-3xl font-bold">FastGram Dashboard</h1>
          </div>

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
          <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-lg mb-8">
            {error}
          </div>
        ) : stats ? (
          <div className="grid grid-cols-5 gap-4 mb-8">
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
        ) : null}

        <LeadsTable key={refreshKey} />
      </div>
    </div>
  );
}
