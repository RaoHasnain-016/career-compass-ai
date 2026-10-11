import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  sendEmailVerification,
  signInWithPopup,
  updateProfile,
} from "firebase/auth";
import { FcGoogle } from "react-icons/fc";
import {
  FaCompass,
  FaEnvelope,
  FaLock,
  FaUser,
} from "react-icons/fa";
import { auth, googleProvider } from "../firebase/firebase";
import { syncFirebaseUser } from "../services/authService";
import "../styles/signup-page.css";

function getSignupErrorMessage(error) {
  switch (error.code) {
    case "auth/email-already-in-use":
      return "An account already exists with this email.";
    case "auth/invalid-email":
      return "Invalid email address.";
    case "auth/weak-password":
      return "Password should be at least 6 characters.";
    case "auth/popup-closed-by-user":
      return "Google popup was closed before completing signup.";
    case "auth/popup-blocked":
      return "Your browser blocked the Google sign-in popup. Allow popups for this site and try again.";
    case "auth/unauthorized-domain":
      return "Google sign-in is not enabled for this address. Open the app using http://localhost:8000 or add this domain in Firebase Authentication settings.";
    case "auth/operation-not-allowed":
      return "Google sign-in is disabled. Enable the Google provider in Firebase Authentication settings.";
    case "auth/network-request-failed":
      return "Google sign-in could not connect. Check your internet connection and try again.";
    case "auth/too-many-requests":
      return "Too many requests. Please wait a few minutes and try again.";
    default:
      return error?.message || "Signup failed. Please try again.";
  }
}

function Signup() {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [agree, setAgree] = useState(false);

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

  const validateForm = () => {
    if (!fullName.trim()) {
      setError("Please enter your full name.");
      return false;
    }

    if (!email.trim()) {
      setError("Please enter your email.");
      return false;
    }

    if (!password) {
      setError("Please enter your password.");
      return false;
    }

    if (password.length < 6) {
      setError("Password should be at least 6 characters.");
      return false;
    }

    if (!confirmPassword) {
      setError("Please confirm your password.");
      return false;
    }

    if (password !== confirmPassword) {
      setError("Password and confirm password do not match.");
      return false;
    }

    if (!agree) {
      setError("Please agree to the Terms and Privacy Policy.");
      return false;
    }

    return true;
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) return;

    try {
      setLoading(true);

      const result = await createUserWithEmailAndPassword(
        auth,
        email.trim(),
        password
      );

      await updateProfile(result.user, {
        displayName: fullName.trim(),
      });

      await result.user.reload();

      localStorage.setItem("selectedRole", "Student");
      localStorage.setItem("signupName", fullName.trim());
      localStorage.setItem("signupEmail", email.trim());

      const activeUser = auth.currentUser;

      if (!activeUser) {
        setError("Account created, but user session was not found.");
        return;
      }

      await syncFirebaseUser(activeUser, fullName.trim());

      await sendEmailVerification(activeUser);

      navigate("/verify-email", { replace: true });
    } catch (error) {
      console.error(error);
      setError(getSignupErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    setError("");

    if (!agree) {
      setError("Please agree to the Terms and Privacy Policy first.");
      return;
    }

    try {
      setGoogleLoading(true);

      const result = await signInWithPopup(auth, googleProvider);

      localStorage.setItem("selectedRole", "Student");

      await syncFirebaseUser(result.user);

      navigate("/dashboard", { replace: true });
    } catch (error) {
      console.error(error);
      setError(getSignupErrorMessage(error));
    } finally {
      setGoogleLoading(false);
    }
  };

  if (checkingAuth) {
    return (
      <div className="auth-check">
        Checking account status...
      </div>
    );
  }

  return (
    <div className="signup-page">
      <div className="signup-shell">
        <motion.div
          className="signup-left"
          initial={{ opacity: 0, x: -35 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.65 }}
        >
          <Link to="/" className="signup-brand">
            <span className="signup-brand-icon">
              <FaCompass />
            </span>
            <span>Career Compass AI</span>
          </Link>

          <div className="signup-card-wrap">
            <motion.div
              className="signup-card"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.1 }}
            >
              <h1>Create your account</h1>
              <p>
                Join us and start mapping your professional journey with AI.
              </p>

              {error && (
                <motion.div
                  className="signup-error"
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  {error}
                </motion.div>
              )}

              <form onSubmit={handleSignup} className="signup-form">
                <div className="signup-field">
                  <label>Full Name</label>
                  <div className="signup-input-wrap">
                    <span className="signup-input-icon">
                      <FaUser />
                    </span>
                    <input
                      type="text"
                      placeholder="John Doe"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      autoComplete="name"
                    />
                  </div>
                </div>

                <div className="signup-field">
                  <label>Email</label>
                  <div className="signup-input-wrap">
                    <span className="signup-input-icon">
                      <FaEnvelope />
                    </span>
                    <input
                      type="email"
                      placeholder="student@university.edu"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      autoComplete="email"
                    />
                  </div>
                </div>

                <div className="signup-password-grid">
                  <div className="signup-field">
                    <label>Password</label>
                    <div className="signup-input-wrap">
                      <span className="signup-input-icon">
                        <FaLock />
                      </span>
                      <input
                        type="password"
                        placeholder="Enter password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="new-password"
                      />
                    </div>
                  </div>

                  <div className="signup-field">
                    <label>Confirm Password</label>
                    <div className="signup-input-wrap">
                      <span className="signup-input-icon">
                        <FaLock />
                      </span>
                      <input
                        type="password"
                        placeholder="Confirm password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        autoComplete="new-password"
                      />
                    </div>
                  </div>
                </div>

                <div className="signup-student-note">
                  This is a student account. Your academic stage and country are collected in the next step.
                </div>

                <label className="signup-check">
                  <input
                    type="checkbox"
                    checked={agree}
                    onChange={(e) => setAgree(e.target.checked)}
                  />
                  <span>
                    I agree to the <Link to="/terms">Terms and Conditions</Link>{" "}
                    and <Link to="/terms">Privacy Policy</Link>.
                  </span>
                </label>

                <button
                  type="submit"
                  className="signup-btn primary"
                  disabled={loading || googleLoading}
                >
                  {loading ? "Creating Account..." : "Create Account"}
                </button>
              </form>

              <div className="signup-divider">
                <span></span>
                <p>OR</p>
                <span></span>
              </div>

              <button
                type="button"
                className="signup-btn google"
                onClick={handleGoogleSignup}
                disabled={loading || googleLoading}
              >
                <FcGoogle />
                {googleLoading ? "Connecting..." : "Continue with Google"}
              </button>

              <p className="signup-footer">
                Already have an account? <Link to="/login">Login</Link>
              </p>
            </motion.div>
          </div>
        </motion.div>

        <motion.div
          className="signup-right"
          initial={{ opacity: 0, x: 35 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.7 }}
        >
          <div className="signup-right-overlay"></div>
          <div className="signup-glow signup-glow-one"></div>
          <div className="signup-glow signup-glow-two"></div>

          <div className="signup-right-content">
            <motion.div
              className="signup-right-badge"
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 2.6, repeat: Infinity }}
            >
              AI-Powered Growth
            </motion.div>

            <motion.div
              className="signup-right-card"
              initial={{ opacity: 0, y: 25 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.25 }}
            >
              <h2>Empower your future</h2>
              <p>
                Leverage AI-driven insights to discover the perfect career path
                tailored to your unique skills and aspirations.
              </p>

              <ul>
                <li>Personalized career recommendations</li>
                <li>Roadmaps built for your goals</li>
                <li>Skill-gap driven learning resources</li>
                <li>Smart AI chatbot support</li>
              </ul>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default Signup;
