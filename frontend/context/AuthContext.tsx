"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import * as api from "@/services/api";
import type { User } from "@/lib/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginDemo: () => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string
  ) => Promise<void>;
  logout: () => void;
}

const DEMO_EMAIL = "demo@risklens.sim";
const DEMO_PASSWORD = "demo1234";

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then((u) => setUser(u))
      .catch(() => {
        api.setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const applyAuth = useCallback(
    (res: { access_token: string; user: User }) => {
      api.setToken(res.access_token);
      setUser(res.user);
    },
    []
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.login(email, password);
      applyAuth(res);
    },
    [applyAuth]
  );

  const loginDemo = useCallback(async () => {
    const res = await api.login(DEMO_EMAIL, DEMO_PASSWORD);
    applyAuth(res);
  }, [applyAuth]);

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      const res = await api.register(email, password, fullName);
      applyAuth(res);
    },
    [applyAuth]
  );

  const logout = useCallback(() => {
    api.setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, loading, login, loginDemo, register, logout }),
    [user, loading, login, loginDemo, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
