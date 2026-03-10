"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { usePathname, useRouter } from "next/navigation";

const TOKEN_URL =
  process.env.NEXT_PUBLIC_TOKEN_SERVICE_URL || "http://localhost:8000";
const STORAGE_KEY = "alloist_admin_jwt";

export interface OrgInfo {
  id: string;
  name: string;
  role: string;
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
}

interface AuthContextValue {
  jwt: string;
  orgId: string | null;
  orgs: OrgInfo[];
  user: UserInfo | null;
  isConfigured: boolean;
  isLoading: boolean;
  loginWithGoogle: () => void;
  loginWithGitHub: () => void;
  logout: () => void;
  setOrgId: (id: string) => void;
  setTokenFromCallback: (token: string) => void;
  fetchMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function parseJwtExp(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp ?? null;
  } catch {
    return null;
  }
}

function isJwtExpired(token: string): boolean {
  const exp = parseJwtExp(token);
  if (!exp) return true;
  return Date.now() >= exp * 1000;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [jwt, setJwt] = useState("");
  const [orgId, setOrgIdState] = useState<string | null>(null);
  const [orgs, setOrgs] = useState<OrgInfo[]>([]);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const pathname = usePathname();
  const router = useRouter();

  const fetchMe = useCallback(async () => {
    if (!jwt) return;
    try {
      const res = await fetch(`${TOKEN_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        setOrgs(data.orgs || []);
        if (data.orgs?.length && !orgId) {
          setOrgIdState(data.orgs[0].id);
        }
      } else {
        setJwt("");
        setUser(null);
        setOrgs([]);
        setOrgIdState(null);
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      setJwt("");
      setUser(null);
      setOrgs([]);
      setOrgIdState(null);
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [jwt, orgId]);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && !isJwtExpired(stored)) {
      setJwt(stored);
    } else if (stored) {
      localStorage.removeItem(STORAGE_KEY);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (jwt && !isJwtExpired(jwt) && !user) {
      fetchMe();
    }
  }, [jwt, user, fetchMe]);

  useEffect(() => {
    if (isLoading) return;
    const isAuthPage = pathname === "/login" || pathname.startsWith("/auth/");
    if (!jwt && !isAuthPage) {
      router.replace("/login");
    }
  }, [isLoading, jwt, pathname, router]);

  const loginWithGoogle = useCallback(() => {
    window.location.href = `${TOKEN_URL}/auth/google/login`;
  }, []);

  const loginWithGitHub = useCallback(() => {
    window.location.href = `${TOKEN_URL}/auth/github/login`;
  }, []);

  const logout = useCallback(() => {
    setJwt("");
    setOrgIdState(null);
    setOrgs([]);
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
    router.replace("/login");
  }, [router]);

  const setOrgId = useCallback((id: string) => {
    setOrgIdState(id);
  }, []);

  const setTokenFromCallback = useCallback((token: string) => {
    localStorage.setItem(STORAGE_KEY, token);
    setJwt(token);
  }, []);

  const value: AuthContextValue = {
    jwt,
    orgId,
    orgs,
    user,
    isConfigured: !!jwt && !isJwtExpired(jwt),
    isLoading,
    loginWithGoogle,
    loginWithGitHub,
    logout,
    setOrgId,
    setTokenFromCallback,
    fetchMe,
  };

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
