import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
} from "firebase/auth";
import { FcGoogle } from "react-icons/fc";
import { FaCompass, FaEnvelope, FaLock } from "react-icons/fa";
import { auth, googleProvider } from "../firebase/firebase";
import { syncFirebaseUser } from "../services/authService";
import "../styles/login-page.css";

function getLoginErrorMessage(error) {
  switch (error.code) {
    case "auth/invalid-email":
      return "Invalid email address.";
    case "auth/user-not-found":
      return "No account found with this email.";
    case "auth/wrong-password":
      return "Incorrect password.";
    case "auth/invalid-credential":
      return "Invalid email or password.";
    case "auth/too-many-requests":
      return "Too many failed attempts. Please try again later.";
    case "auth/popup-closed-by-user":
      return "Google popup was closed before completing sign in.";
    case "auth/popup-blocked":
      return "Your browser blocked the Google sign-in popup. Allow popups for this site and try again.";
    case "auth/unauthorized-domain":
      return "Google sign-in is not enabled for this address. Open the app using http://localhost:8000 or add this domain in Firebase Authentication settings.";
    case "auth/operation-not-allowed":
      return "Google sign-in is disabled. Enable the Google provider in Firebase Authentication settings.";
    case "auth/network-request-failed":
      return "Google sign-in could not connect. Check your internet connection and try again.";
    default:
      return error?.message || "Login failed. Please try again.";
  }
}

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from?.pathname || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [checkingAuth, setCheckingAuth] = useState(true);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      if (!currentUser) {
        setCheckingAuth(false);
        return;
      }

      await currentUser.reload();

      if (auth.currentUser?.emailVerified) {
        try {
          await syncFirebaseUser(auth.currentUser);
        } catch (error) {
          console.error("Backend sync failed:", error);
        }

        navigate("/dashboard", { replace: true });
      } else {
        navigate("/verify-email", { replace: true });
      }
    });

    return () => unsubscribe();
  }, [navigate]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Please enter email and password.");
      return;
    }

    try {
      setLoading(true);

      const result = await signInWithEmailAndPassword(
        auth,
        email.trim(),
        password
      );

      await result.user.reload();

      if (!auth.currentUser?.emailVerified) {
        navigate("/verify-email", { replace: true });
        return;
      }

      await syncFirebaseUser(auth.currentUser);

      navigate(redirectTo, { replace: true });
    } catch (error) {
      console.error(error);
      setError(getLoginErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError("");

    try {
      setGoogleLoading(true);

      const result = await signInWithPopup(auth, googleProvider);

      await syncFirebaseUser(result.user);

      navigate(redirectTo, { replace: true });
    } catch (error) {
      console.error(error);
      setError(getLoginErrorMessage(error));
    } finally {
      setGoogleLoading(false);
    }
  };

  if (checkingAuth) {
    return <div className="auth-check">Checking account status...</div>;
  }

  return (
    <div className="login-page">
      <div className="login-shell">
        <motion.div
          className="login-left"
          initial={{ opacity: 0, x: -35 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.65 }}
        >
          <Link to="/" className="login-brand">
            <span className="brand-icon">
              <FaCompass />
            </span>
            <span>Career Compass AI</span>
          </Link>

          <div className="login-form-wrap">
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.1 }}
            >
              <h1 className="login-title">Welcome back</h1>
              <p className="login-subtitle">
                Please enter your details to sign in.
              </p>
            </motion.div>

            {error && (
              <motion.div
                className="login-error"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {error}
              </motion.div>
            )}

            <form onSubmit={handleLogin} className="login-form">
              <div className="login-field">
                <label>Email</label>
                <div className="input-wrap">
                  <span className="input-icon">
                    <FaEnvelope />
                  </span>
                  <input
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                  />
                </div>
              </div>

              <div className="login-field">
                <label>Password</label>
                <div className="input-wrap">
                  <span className="input-icon">
                    <FaLock />
                  </span>
                  <input
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                  />
                </div>
              </div>

              <div className="login-meta">
                <Link to="/forgot-password" className="forgot-link">
                  Forgot password?
                </Link>
              </div>

              <button
                type="submit"
                className="login-btn primary"
                disabled={loading || googleLoading}
              >
                {loading ? "Logging in..." : "Login"}
              </button>
            </form>

            <div className="login-divider">
              <span></span>
              <p>OR</p>
              <span></span>
            </div>

            <button
              type="button"
              className="login-btn google"
              onClick={handleGoogleLogin}
              disabled={loading || googleLoading}
            >
              <FcGoogle />
              {googleLoading ? "Connecting..." : "Continue with Google"}
            </button>

            <p className="login-footer-text">
              Don&apos;t have an account? <Link to="/signup">Sign up</Link>
            </p>
          </div>
        </motion.div>

        <motion.div
          className="login-right"
          initial={{ opacity: 0, x: 35 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.7 }}
        >
          <div className="login-right-overlay"></div>

          <div className="login-glow login-glow-one"></div>
          <div className="login-glow login-glow-two"></div>

          <div className="login-quote-wrap">
            <motion.div
              className="sparkles"
              animate={{ y: [0, -8, 0], opacity: [0.75, 1, 0.75] }}
              transition={{ duration: 2.8, repeat: Infinity }}
            >
              ✦ ✦
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.25 }}
            >
              "Your future is created by what you do today, not tomorrow."
            </motion.h2>

            <motion.div
              className="quote-line"
              initial={{ width: 0 }}
              animate={{ width: "90px" }}
              transition={{ duration: 0.7, delay: 0.45 }}
            />

            <motion.div
              className="login-info-card"
              initial={{ opacity: 0, y: 25 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.4 }}
            >
              <div className="info-badge">AI Career Guidance</div>
              <h3>Smarter career decisions start here</h3>
              <ul>
                <li>Personalized recommendations</li>
                <li>Career roadmaps</li>
                <li>Skill-gap analysis</li>
                <li>AI chatbot support</li>
              </ul>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default Login;
