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
      // Fixed: removed unused error variable
      setStatus(false);
      toast.error("Session check error");
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
        toast.success("Session successfully created!");
        setIsChallenge(false);
        setVerificationCode("");
        fetchStatus();
      } else if (res.status === "challenge_required") {
        setIsChallenge(true);
        toast.error("2FA code required");
      }
    } catch (error: unknown) {
      // Fixed: any replaced with safe unknown
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("Authorization error");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageWrapper title="Session Management">
      <div className="bg-card border border-border rounded-lg p-6 max-w-2xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-xl font-semibold mb-2">
              Instagram Session Status
            </h2>
            <p className="text-muted-foreground text-sm">
              Here you can check the status of the current session or initiate a new one.
            </p>
          </div>
          <Button onClick={fetchStatus} disabled={isLoading} variant="outline">
            <RefreshCw
              className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
            />
            Check
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
                ? "Session Active"
                : status === false
                  ? "Invalid Session"
                  : "Checking..."}
            </div>
            {createdAt && status === true && (
              <div className="text-sm text-muted-foreground mt-1">
                Created: {formatDate(createdAt)}
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-border pt-6">
          <h3 className="font-medium mb-4">Create new session</h3>

          {isChallenge && (
            <div className="mb-4">
              <label className="block text-sm text-muted-foreground mb-2">
                2FA Code
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
            {isChallenge ? "Send code" : "Initiate login"}
          </Button>
        </div>
      </div>
    </PageWrapper>
  );
}
