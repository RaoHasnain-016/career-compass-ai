import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  onAuthStateChanged,
  sendEmailVerification,
  signOut,
} from "firebase/auth";
import {
  FaCheckCircle,
  FaCompass,
  FaEnvelopeOpenText,
  FaPaperPlane,
  FaRedoAlt,
  FaShieldAlt,
  FaSignOutAlt,
} from "react-icons/fa";
import { auth } from "../firebase/firebase";
import "../styles/email-verification.css";

function EmailVerification() {
  const navigate = useNavigate();

  const [currentUser, setCurrentUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setChecking(true);

      if (!user) {
        navigate("/login", { replace: true });
        return;
      }

      await user.reload();

      if (auth.currentUser?.emailVerified) {
        navigate("/dashboard", { replace: true });
        return;
      }

      setCurrentUser(auth.currentUser);
      setChecking(false);
    });

    return () => unsubscribe();
  }, [navigate]);

  const handleSendVerification = async () => {
    setError("");
    setMessage("");

    if (!auth.currentUser) {
      setError("No logged-in user found. Please login again.");
      return;
    }

    try {
      setSending(true);

      await sendEmailVerification(auth.currentUser);

      setMessage(
        "Verification email sent successfully. Please check your inbox or spam folder."
      );
    } catch (error) {
      console.error(error);

      if (error.code === "auth/too-many-requests") {
        setError("Too many requests. Please wait a few minutes and try again.");
      } else {
        setError("Failed to send verification email. Please try again.");
      }
    } finally {
      setSending(false);
    }
  };

  const handleCheckVerification = async () => {
    setError("");
    setMessage("");

    if (!auth.currentUser) {
      setError("No logged-in user found. Please login again.");
      return;
    }

    try {
      setVerifying(true);

      await auth.currentUser.reload();

      if (auth.currentUser.emailVerified) {
        setMessage("Email verified successfully. Redirecting to dashboard...");

        setTimeout(() => {
          navigate("/dashboard", { replace: true });
        }, 900);
      } else {
        setError(
          "Your email is not verified yet. Please open the verification link from your email."
        );
      }
    } catch (error) {
      console.error(error);
      setError("Could not check verification status. Please try again.");
    } finally {
      setVerifying(false);
    }
  };

  const handleChangeAccount = async () => {
    await signOut(auth);
    navigate("/login", { replace: true });
  };

  if (checking) {
    return (
      <div className="email-verify-loading">
        <div className="verify-loader"></div>
        <p>Checking verification status...</p>
      </div>
    );
  }

  return (
    <div className="email-verify-page">
      <div className="email-verify-shell">
        <motion.div
          className="email-verify-left"
          initial={{ opacity: 0, x: -35 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.65 }}
        >
          <Link to="/" className="email-verify-brand">
            <span className="email-verify-brand-icon">
              <FaCompass />
            </span>
            <span>Career Compass AI</span>
          </Link>

          <div className="email-verify-left-content">
            <motion.div
              className="verify-badge"
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 2.6, repeat: Infinity }}
            >
              Secure Account Setup
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.12 }}
            >
              Verify your email to unlock your AI career journey
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.2 }}
            >
              We use email verification to keep your account secure and make
              sure your personalized career profile stays protected.
            </motion.p>

            <motion.div
              className="verify-feature-list"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.28 }}
            >
              <div className="verify-feature-item">
                <span>
                  <FaShieldAlt />
                </span>
                <div>
                  <h4>Secure account access</h4>
                  <p>Protect your profile, recommendations, and saved careers.</p>
                </div>
              </div>

              <div className="verify-feature-item">
                <span>
                  <FaEnvelopeOpenText />
                </span>
                <div>
                  <h4>Confirm your identity</h4>
                  <p>Verify your email before entering your student dashboard.</p>
                </div>
              </div>

              <div className="verify-feature-item">
                <span>
                  <FaCheckCircle />
                </span>
                <div>
                  <h4>Start your roadmap</h4>
                  <p>After verification, continue to your AI-powered dashboard.</p>
                </div>
              </div>
            </motion.div>
          </div>

          <div className="email-verify-glow email-verify-glow-one"></div>
          <div className="email-verify-glow email-verify-glow-two"></div>
        </motion.div>

        <motion.div
          className="email-verify-right"
          initial={{ opacity: 0, x: 35 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.7 }}
        >
          <motion.div
            className="email-verify-card"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.14 }}
          >
            <motion.div
              className="email-verify-icon"
              animate={{ rotate: [0, -5, 5, 0], scale: [1, 1.04, 1] }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <FaEnvelopeOpenText />
            </motion.div>

            <h1>Verify your email</h1>

            <p>
              We sent a verification link to your email. Open the link, then
              come back and click the verification check button.
            </p>

            <div className="verify-email-box">
              <span>Email Address</span>
              <strong>{currentUser?.email || "Not available"}</strong>
            </div>

            {message && (
              <motion.div
                className="verify-message success"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {message}
              </motion.div>
            )}

            {error && (
              <motion.div
                className="verify-message error"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {error}
              </motion.div>
            )}

            <div className="verify-actions">
              <button
                type="button"
                className="verify-btn primary"
                onClick={handleCheckVerification}
                disabled={verifying || sending}
              >
                <FaCheckCircle />
                {verifying ? "Checking..." : "I have verified"}
              </button>

              <button
                type="button"
                className="verify-btn secondary"
                onClick={handleSendVerification}
                disabled={sending || verifying}
              >
                {sending ? <FaRedoAlt className="spin-icon" /> : <FaPaperPlane />}
                {sending ? "Sending..." : "Resend email"}
              </button>
            </div>

            <button
              type="button"
              className="verify-change-account"
              onClick={handleChangeAccount}
            >
              <FaSignOutAlt />
              Use another account
            </button>

            <p className="verify-help-text">
              Didn&apos;t receive it? Check your spam folder or resend the
              verification email.
            </p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

export default EmailVerification;