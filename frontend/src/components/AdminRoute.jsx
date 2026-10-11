import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { getCurrentBackendUser } from "../services/authService";

export default function AdminRoute({ children }) {
  const [allowed, setAllowed] = useState(null);

  useEffect(() => {
    let active = true;
    getCurrentBackendUser()
      .then((user) => active && setAllowed(user?.role?.toLowerCase() === "admin"))
      .catch(() => active && setAllowed(false));
    return () => { active = false; };
  }, []);

  if (allowed === null) return <div className="auth-check">Checking access...</div>;
  return allowed ? children : <Navigate to="/dashboard" replace />;
}
