import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FaEdit, FaUser } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { auth } from "../firebase/firebase";
import { getStudentProfile } from "../services/profileService";
import "../styles/student-profile-page.css";

function asArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") return value.split(",").map((item) => item.trim()).filter(Boolean);
  return [];
}

export default function StudentProfile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadProfile() {
      try {
        setLoading(true);
        setError("");
        const data = await getStudentProfile();
        if (active) setProfile(data);
      } catch (error) {
        console.error(error);
        if (active) setError(error.message || "Profile could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadProfile();

    return () => {
      active = false;
    };
  }, []);

  const completion = useMemo(() => {
    if (!profile) return 0;
    const checks = [
      profile.age,
      profile.academic_level,
      profile.class_degree,
      profile.marks_cgpa,
      asArray(profile.favorite_subjects).length,
      asArray(profile.weak_subjects).length,
      asArray(profile.interests).length,
      asArray(profile.skills).length,
      profile.study_preference,
    ];
    return Math.round((checks.filter(Boolean).length / checks.length) * 100);
  }, [profile]);

  if (loading) {
    return (
      <StudentLayout>
        <div className="cc-loading">
          <div className="cc-loader">
            <FaUser />
          </div>
          <h2>Loading profile...</h2>
          <p>Fetching your student profile from the backend.</p>
        </div>
      </StudentLayout>
    );
  }

  if (!profile) {
    return (
      <StudentLayout>
        <div className="cc-empty">
          <FaUser />
          <h2>No profile found</h2>
          <p>{error || "Complete profile setup to unlock personalized guidance."}</p>
          <Link className="cc-btn" to="/profile-setup">
            Complete Profile
          </Link>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout className="student-profile-page">
      <header className="cc-page-header">
        <div>
          <h1>Student Profile</h1>
          <p>Live academic, interest, and skill data used by Career Compass AI.</p>
        </div>
        <Link className="cc-btn" to="/profile-setup">
          <FaEdit />
          Edit Profile
        </Link>
      </header>

      <section className="profile-identity-card">
        <img src={auth.currentUser?.photoURL || "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=160&q=80"} alt="Profile" />
        <div>
          <h2>{auth.currentUser?.displayName || auth.currentUser?.email?.split("@")[0] || "Student"}</h2>
          <p>{auth.currentUser?.email}</p>
          <div className="profile-progress">
            <span style={{ width: `${completion}%` }}></span>
          </div>
          <small>{completion}% profile completion</small>
        </div>
      </section>

      <div className="profile-info-grid">
        <section className="cc-card">
          <h2>Academic Information</h2>
          <dl>
            <dt>Age</dt>
            <dd>{profile.age || "Not added"}</dd>
            <dt>Country / System</dt>
            <dd>{profile.country || "Not added"}</dd>
            <dt>Academic Level</dt>
            <dd>{profile.academic_level || "Not added"}</dd>
            <dt>Class / Degree</dt>
            <dd>{profile.class_degree || "Not added"}</dd>
            <dt>Marks / CGPA</dt>
            <dd>{profile.marks_cgpa ?? "Not added"}</dd>
            <dt>Study Preference</dt>
            <dd>{profile.study_preference || "Not added"}</dd>
          </dl>
        </section>

        <section className="cc-card">
          <h2>Favorite Subjects</h2>
          <div className="cc-chip-list">
            {asArray(profile.favorite_subjects).map((item) => <span key={item}>{item}</span>)}
          </div>
          <h2>Weak Subjects</h2>
          <div className="cc-chip-list weak">
            {asArray(profile.weak_subjects).map((item) => <span key={item}>{item}</span>)}
          </div>
        </section>

        <section className="cc-card">
          <h2>Interests</h2>
          <div className="cc-chip-list">
            {asArray(profile.interests).map((item) => <span key={item}>{item}</span>)}
          </div>
        </section>

        <section className="cc-card">
          <h2>Skills</h2>
          <div className="cc-chip-list">
            {asArray(profile.skills).map((item) => <span key={item}>{item}</span>)}
          </div>
        </section>
      </div>
    </StudentLayout>
  );
}
