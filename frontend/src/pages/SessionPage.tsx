import { useState, useEffect } from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { Button } from "@/components/ui/button";
import { checkAuthStatus, triggerLogin } from "@/api/auth";
import { ShieldAlert, ShieldCheck, RefreshCw, KeyRound } from "lucide-react";
import { formatDate } from "@/lib/formatters";
import toast from "react-hot-toast";

export default function SessionPage() {
  const [status, setStatus] = useState<boolean | null>(null);
  const [createdAt, setCreatedAt] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isChallenge, setIsChallenge] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");

  const fetchStatus = async () => {
    setIsLoading(true);
    try {
      const res = await checkAuthStatus();
      setStatus(res.is_valid);
      setCreatedAt(res.session_created_at || null);
    } catch {
      // Виправлено: видалено невикористану змінну error
      setStatus(false);
      toast.error("Помилка перевірки сесії");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchStatus();
  }, []);

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      const res = await triggerLogin(verificationCode || undefined);
      if (res.status === "success") {
        toast.success("Сесія успішно створена!");
        setIsChallenge(false);
        setVerificationCode("");
        fetchStatus();
      } else if (res.status === "challenge_required") {
        setIsChallenge(true);
        toast.error("Потрібен код 2FA");
      }
    } catch (error: unknown) {
      // Виправлено: any замінено на безпечний unknown
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("Помилка авторизації");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageWrapper title="Управління сесією">
      <div className="bg-card border border-border rounded-lg p-6 max-w-2xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-xl font-semibold mb-2">
              Статус Instagram Сесії
            </h2>
            <p className="text-muted-foreground text-sm">
              Тут ви можете перевірити активність поточної сесії або ініціювати
              нову.
            </p>
          </div>
          <Button onClick={fetchStatus} disabled={isLoading} variant="outline">
            <RefreshCw
              className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
            />
            Перевірити
          </Button>
        </div>

        <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50 mb-8">
          {status === true ? (
            <ShieldCheck className="w-12 h-12 text-emerald-500" />
          ) : status === false ? (
            <ShieldAlert className="w-12 h-12 text-red-500" />
          ) : (
            <div className="w-12 h-12 rounded-full border-4 border-muted-foreground border-t-transparent animate-spin" />
          )}

          <div>
            <div className="font-medium text-lg">
              {status === true
                ? "Сесія Активна"
                : status === false
                  ? "Сесія Невалідна"
                  : "Перевірка..."}
            </div>
            {createdAt && status === true && (
              <div className="text-sm text-muted-foreground mt-1">
                Створена: {formatDate(createdAt)}
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-border pt-6">
          <h3 className="font-medium mb-4">Створення нової сесії</h3>

          {isChallenge && (
            <div className="mb-4">
              <label className="block text-sm text-muted-foreground mb-2">
                Код 2FA
              </label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  className="w-full bg-background border border-border rounded-md py-2 pl-9 pr-4"
                  placeholder="123456"
                />
              </div>
            </div>
          )}

          <Button
            onClick={handleLogin}
            disabled={isLoading}
            className="w-full sm:w-auto"
          >
            {isChallenge ? "Відправити код" : "Ініціювати логін"}
          </Button>
        </div>
      </div>
    </PageWrapper>
  );
}
