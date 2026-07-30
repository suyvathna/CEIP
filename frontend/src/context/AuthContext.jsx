import { createContext, useContext, useState } from "react";
import {
  login as apiLogin,
  logout as apiLogout,
  isLoggedIn as checkIsLoggedIn,
} from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [loggedIn, setLoggedIn] = useState(checkIsLoggedIn());

  async function login(email, password) {
    await apiLogin(email, password);
    setLoggedIn(true);
  }

  function logout() {
    apiLogout();
    setLoggedIn(false);
  }

  return (
    <AuthContext.Provider value={{ loggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}