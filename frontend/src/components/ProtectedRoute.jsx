import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "../firebase/firebase";
import { syncFirebaseUser } from "../services/authService";

function isGoogleUser(user) {
  return user?.providerData?.some((provider) => provider.providerId === "google.com");
}

export default function ProtectedRoute({ children }) {
  const location = useLocation();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [user, setUser] = useState(null);
  const [needsVerification, setNeedsVerification] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setCheckingAuth(true);

      if (currentUser) {
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
