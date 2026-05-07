import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signOut } from "firebase/auth";
import { FaCog, FaSignOutAlt, FaUser } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { auth } from "../firebase/firebase";
import "../styles/settings-page.css";

export default function Settings() {
  const navigate = useNavigate();
  const [signingOut, setSigningOut] = useState(false);

  const handleSignOut = async () => {
    setSigningOut(true);
    await signOut(auth);
    navigate("/login", { replace: true });
  };

  return (
    <StudentLayout className="settings-page">
      <header className="cc-page-header">
        <div>
          <h1>Settings</h1>
          <p>Manage account details and quick actions for your Career Compass AI workspace.</p>
        </div>
      </header>

      <div className="settings-grid">
        <section className="settings-account-card">
          <img src={auth.currentUser?.photoURL || "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=160&q=80"} alt="Account" />
          <div>
            <h2>{auth.currentUser?.displayName || "Student"}</h2>
            <p>{auth.currentUser?.email || "No email available"}</p>
            <span>{auth.currentUser?.emailVerified ? "Verified account" : "Email verification pending"}</span>
          </div>
        </section>

        <section className="cc-card settings-actions-card">
          <h2>
            <FaCog />
            Account Actions
          </h2>
          <div className="settings-action-list">
            <Link className="cc-btn secondary" to="/profile-setup">
              <FaUser />
              Edit Student Profile
            </Link>
            <button className="cc-btn danger" type="button" onClick={handleSignOut} disabled={signingOut}>
              <FaSignOutAlt />
              {signingOut ? "Signing out..." : "Sign Out"}
            </button>
          </div>
        </section>
      </div>
    </StudentLayout>
  );
}
