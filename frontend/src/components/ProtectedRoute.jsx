import { useEffect, useRef, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "../firebase/firebase";
import { syncFirebaseUser } from "../services/authService";

function isGoogleUser(user) {
  return user?.providerData?.some((provider) => provider.providerId === "google.com");
}

const INACTIVITY_TIMEOUT_MS = 20 * 60 * 1000;

export default function ProtectedRoute({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [user, setUser] = useState(null);
  const [needsVerification, setNeedsVerification] = useState(false);
  const lastActivityRef = useRef(Date.now());
  const timeoutRef = useRef(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setCheckingAuth(true);

      if (currentUser && !isGoogleUser(currentUser)) {
        try {
          await currentUser.reload();
        } catch (error) {
          console.error("Firebase reload failed:", error);
        }
      }

      setUser(currentUser);
      setNeedsVerification(
        Boolean(
          currentUser &&
            !auth.currentUser?.emailVerified &&
            !isGoogleUser(auth.currentUser)
        )
      );

      if (
        currentUser &&
        (auth.currentUser?.emailVerified || isGoogleUser(auth.currentUser))
      ) {
        try {
          await syncFirebaseUser(auth.currentUser);
        } catch (error) {
          console.error("Backend sync failed:", error);
        }
      }

      setCheckingAuth(false);
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (checkingAuth || !user || needsVerification) return undefined;

    let loggingOut = false;

    const clearIdleTimer = () => {
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    };

    const expireSession = async () => {
      if (loggingOut) return;
      loggingOut = true;
      clearIdleTimer();
      try {
        await signOut(auth);
      } finally {
        navigate("/login", {
          replace: true,
          state: { from: location, sessionExpired: true },
        });
      }
    };

    const scheduleTimeout = () => {
      clearIdleTimer();
      const remaining = INACTIVITY_TIMEOUT_MS - (Date.now() - lastActivityRef.current);
      timeoutRef.current = window.setTimeout(expireSession, Math.max(0, remaining));
    };

    const recordActivity = () => {
      lastActivityRef.current = Date.now();
      scheduleTimeout();
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState !== "visible") return;
      if (Date.now() - lastActivityRef.current >= INACTIVITY_TIMEOUT_MS) {
        expireSession();
      } else {
        scheduleTimeout();
      }
    };

    ["pointerdown", "keydown", "touchstart", "scroll"].forEach((eventName) =>
      window.addEventListener(eventName, recordActivity, { passive: true })
    );
    document.addEventListener("visibilitychange", handleVisibilityChange);
    scheduleTimeout();

    return () => {
      clearIdleTimer();
      ["pointerdown", "keydown", "touchstart", "scroll"].forEach((eventName) =>
        window.removeEventListener(eventName, recordActivity)
      );
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [checkingAuth, location, navigate, needsVerification, user]);

  if (checkingAuth) {
    return <div className="auth-check">Checking authentication...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (needsVerification) {
    return <Navigate to="/verify-email" replace state={{ from: location }} />;
  }

  return children;
}
