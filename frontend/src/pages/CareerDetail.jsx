import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FaBookmark,
  FaBrain,
  FaChartLine,
  FaExclamationTriangle,
  FaRobot,
  FaRoute,
} from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { getCareer } from "../services/recommendationService";
import { saveCareer } from "../services/savedCareerService";
import "../styles/career-detail-page.css";

function asArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") return value.split(",").map((item) => item.trim()).filter(Boolean);
  return [];
}

function normalizeCareer(data) {
  if (!data) return null;
  return data.career || data;
}

export default function CareerDetail() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const stateRecommendation = location.state?.recommendation || null;

  const [career, setCareer] = useState(normalizeCareer(stateRecommendation));
  const [loading, setLoading] = useState(!stateRecommendation);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let active = true;

    async function loadCareer() {
      if (!id) return;

      try {
        setLoading(true);
        setError("");
        const response = await getCareer(id);

        if (active) {
          setCareer(normalizeCareer(response));
        }
      } catch (error) {
        console.error(error);

        if (active && !stateRecommendation) {
          setError(error.message || "Career details could not be loaded.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadCareer();

    return () => {
      active = false;
    };
  }, [id, stateRecommendation]);

  const careerId = career?.career_id || id;
  const title = career?.title || career?.career_title || "Career Detail";
  const matchScore = Math.round(Number(career?.match_score || career?.score || 0));

  const handleSave = async () => {
    try {
      setSaving(true);
      setError("");
      await saveCareer(careerId);
      setMessage("Career saved to your shortlist.");
    } catch (error) {
      console.error(error);
      setError(error.message || "Career could not be saved.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <StudentLayout>
        <div className="cc-loading">
          <div className="cc-loader">
            <FaBrain />
          </div>
          <h2>Loading career details...</h2>
          <p>Fetching the selected career path from the backend.</p>
        </div>
      </StudentLayout>
    );
  }

  if (!career) {
    return (
      <StudentLayout>
        <div className="cc-empty">
          <FaExclamationTriangle />
          <h2>Career not found</h2>
          <p>{error || "Open a recommendation first or generate new recommendations."}</p>
          <Link className="cc-btn" to="/recommendations">
            Open Recommendations
          </Link>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout className="career-detail-page">
      <header className="cc-page-header">
        <div>
          <h1>{title}</h1>
          <p>{career.overview || career.explanation || "Career details are available from your recommendation data."}</p>
        </div>

        <div className="cc-actions">
          <button className="cc-btn secondary" type="button" onClick={handleSave} disabled={saving}>
            <FaBookmark />
            {saving ? "Saving..." : "Save Career"}
          </button>
          <Link className="cc-btn" to={`/roadmap?careerId=${careerId}`} state={{ careerId, careerTitle: title }}>
            <FaRoute />
            View Roadmap
          </Link>
          <Link className="cc-btn secondary" to="/chatbot" state={{ careerId, careerTitle: title }}>
            <FaRobot />
            Ask AI
          </Link>
        </div>
      </header>

      {(error || message) && (
        <div className={error ? "career-message error" : "career-message success"}>
          {error || message}
        </div>
      )}

      <div className="career-detail-grid">
        <motion.section className="cc-card career-overview-card" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
          <span className="career-field">{career.field || "Career Field"}</span>
          <h2>Overview</h2>
          <p>{career.overview || "No overview has been added for this career yet."}</p>

          <div className="career-facts">
            <div>
              <small>Match Score</small>
              <strong>{matchScore ? `${matchScore}%` : "N/A"}</strong>
            </div>
            <div>
              <small>Difficulty</small>
              <strong>{career.difficulty_level || "Not set"}</strong>
            </div>
            <div>
              <small>Eligibility</small>
              <strong>{career.eligibility_status || "Profile based"}</strong>
            </div>
          </div>
        </motion.section>

        <motion.aside className="cc-card career-scope-card" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
          <FaChartLine />
          <h2>Future Scope</h2>
          <p>{career.future_scope || "Future scope data is not available for this career yet."}</p>
        </motion.aside>
      </div>

      <div className="cc-grid two">
        <section className="cc-card">
          <h2>Required Skills</h2>
          <div className="cc-chip-list">
            {(asArray(career.required_skills).length ? asArray(career.required_skills) : asArray(career.matched_skills)).map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </section>

        <section className="cc-card">
          <h2>Required Subjects</h2>
          <div className="cc-chip-list">
            {(asArray(career.required_subjects).length ? asArray(career.required_subjects) : asArray(career.matched_subjects)).map((subject) => (
              <span key={subject}>{subject}</span>
            ))}
          </div>
        </section>
      </div>

      {career.improvement_advice && (
        <section className="cc-card career-advice-card">
          <h2>Improvement Advice</h2>
          <p>{career.improvement_advice}</p>
        </section>
      )}
    </StudentLayout>
  );
}
