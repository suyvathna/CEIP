import { Outlet, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Layout() {
  const { loggedIn, logout } = useAuth();

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="app-header-links">
          <Link to="/" className="app-title">CEIP</Link>
          {loggedIn && <Link to="/deadlines">Deadlines</Link>}
        </div>
        {loggedIn ? (
          <button onClick={logout}>Log Out</button>
        ) : (
          <Link to="/login">Log In</Link>
        )}
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;