import React, { createContext, useState, useEffect } from "react";
import apiFetch from './api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  const isAuthenticated = !!user?.username;

  // On mount, verify cookie-based session with backend
  useEffect(() => {
    const verify = async () => {
      try {
        const res = await apiFetch('/me');
        if (!res.ok) return setUser(null);
        const data = await res.json();
        if (data.authenticated && data.user) {
          setUser({ username: data.user.username, role: data.user.role });
        } else {
          setUser(null);
        }
      } catch (e) {
        setUser(null);
      }
    };
    verify();
  }, []);

  // login: accepts { email, password } or { username, password }
  const login = async (credentials) => {
    try {
      const res = await apiFetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        return { success: false, message: err.error || 'Login failed' };
      }

      // backend sets HttpOnly cookie; fetch /me to populate user
      const me = await fetch('/me', { credentials: 'include' });
      if (!me.ok) return { success: false, message: 'Failed to verify session' };
      const data = await me.json();
      if (data.authenticated && data.user) {
        setUser({ username: data.user.username, role: data.user.role });
        return { success: true };
      }
      return { success: false, message: 'Authentication failed' };
    } catch (err) {
      return { success: false, message: 'Network error' };
    }
  };

  const logout = async () => {
    try {
      // attempt to clear cookie on server; if missing, just clear client state
      await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
    } catch (e) {
      // ignore
    }
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;