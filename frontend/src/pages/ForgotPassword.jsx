import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { sendPasswordResetEmail } from "firebase/auth";
import {
  FaArrowLeft,
  FaArrowRight,
  FaCompass,
  FaEnvelope,
  FaKey,
  FaShieldAlt,
  FaLock,
} from "react-icons/fa";
import { auth } from "../firebase/firebase";
import "../styles/forgot-password.css";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }

    try {
      setLoading(true);
      await sendPasswordResetEmail(auth, email.trim());

      setSuccess(
        "Password reset link has been sent to your email. Please check your inbox."
      );
      setEmail("");
    } catch (error) {
      console.error(error);

      if (error.code === "auth/invalid-email") {
        setError("Invalid email address.");
      } else if (error.code === "auth/user-not-found") {
        setError("No account found with this email.");
      } else if (error.code === "auth/too-many-requests") {
        setError("Too many requests. Please try again later.");
      } else {
        setError("Failed to send reset email. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forgot-page">
      <div className="forgot-shell">
        {/* LEFT SIDE */}
        <motion.div
          className="forgot-left"
          initial={{ opacity: 0, x: -35 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.65 }}
        >
          <Link to="/" className="forgot-brand">
            <span className="forgot-brand-icon">
              <FaCompass />
            </span>
            <span>Career Compass AI</span>
          </Link>

          <div className="forgot-left-content">
            <motion.div
              className="forgot-badge"
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 2.5, repeat: Infinity }}
            >
              Secure Recovery
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15 }}
            >
              Recover access to your account safely
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.22 }}
            >
              Don’t worry — we’ll help you securely reset your password and get
              back to your personalized AI career journey.
            </motion.p>

            <motion.div
              className="forgot-feature-list"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              <div className="forgot-feature-item">
                <span>
                  <FaShieldAlt />
                </span>
                <div>
                  <h4>Protected reset flow</h4>
                  <p>Your recovery process is handled securely through Firebase.</p>
                </div>
              </div>

              <div className="forgot-feature-item">
                <span>
                  <FaLock />
                </span>
                <div>
                  <h4>Fast & reliable</h4>
                  <p>Receive a reset link instantly in your registered email.</p>
                </div>
              </div>

              <div className="forgot-feature-item">
                <span>
                  <FaKey />
                </span>
                <div>
                  <h4>Easy account recovery</h4>
                  <p>Reset your password and continue your career planning.</p>
                </div>
              </div>
            </motion.div>
          </div>

          <div className="forgot-glow forgot-glow-one"></div>
          <div className="forgot-glow forgot-glow-two"></div>
        </motion.div>

        {/* RIGHT SIDE */}
        <motion.div
          className="forgot-right"
          initial={{ opacity: 0, x: 35 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.7 }}
        >
          <motion.div
            className="forgot-card"
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.15 }}
          >
            <div className="forgot-icon-wrap">
              <FaKey />
            </div>

            <h1>Reset Your Password</h1>
            <p>
              Enter your email address and we’ll send you a secure link to reset
              your password.
            </p>

            {error && (
              <motion.div
                className="forgot-message error"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {error}
              </motion.div>
            )}

            {success && (
              <motion.div
                className="forgot-message success"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {success}
              </motion.div>
            )}

            <form onSubmit={handleResetPassword} className="forgot-form">
              <div className="forgot-field">
                <label>Email Address</label>
                <div className="forgot-input-wrap">
                  <span className="forgot-input-icon">
                    <FaEnvelope />
                  </span>
                  <input
                    type="email"
                    placeholder="name@university.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="forgot-btn primary"
                disabled={loading}
              >
                {loading ? "Sending Reset Link..." : "Send Reset Link"}
                {!loading && <FaArrowRight />}
              </button>
            </form>

            <Link to="/login" className="forgot-back-link">
              <FaArrowLeft />
              Back to Login
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

export default ForgotPassword;