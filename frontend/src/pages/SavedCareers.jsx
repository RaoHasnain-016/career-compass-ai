import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FaBookmark, FaTrashAlt } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { getSavedCareers, removeSavedCareer } from "../services/savedCareerService";
import "../styles/saved-careers-page.css";

export default function SavedCareers() {
  const [careers, setCareers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState("");
  const [error, setError] = useState("");

  async function loadSavedCareers() {
    try {
      setLoading(true);
      setError("");
      setCareers(await getSavedCareers());
    } catch (error) {
      console.error(error);
      setError(error.message || "Saved careers could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSavedCareers();
  }, []);

  const handleRemove = async (careerId) => {
    try {
      setRemovingId(careerId);
      await removeSavedCareer(careerId);
      setCareers((prev) => prev.filter((item) => item.career_id !== careerId));
    } catch (error) {
      console.error(error);
      setError(error.message || "Saved career could not be removed.");
    } finally {
      setRemovingId("");
    }
  };

  if (loading) {
    return (
      <StudentLayout>
        <div className="cc-loading">
          <div className="cc-loader">
            <FaBookmark />
          </div>
          <h2>Loading saved careers...</h2>
          <p>Fetching your personal shortlist from the backend.</p>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout className="saved-careers-page">
      <header className="cc-page-header">
        <div>
          <h1>Saved Careers</h1>
          <p>Your private shortlist of careers saved from AI recommendations.</p>
        </div>
        <Link className="cc-btn" to="/recommendations">
          Find Careers
        </Link>
      </header>

      {error && <div className="saved-error">{error}</div>}

      {careers.length === 0 ? (
        <div className="cc-empty">
          <FaBookmark />
          <h2>No saved careers yet</h2>
          <p>Save promising career paths from your recommendations to compare and revisit them.</p>
          <Link className="cc-btn" to="/recommendations">
            Open Recommendations
          </Link>
        </div>
      ) : (
        <div className="saved-career-grid">
          {careers.map((career, index) => (
            <motion.article
              key={career.saved_id || career.career_id}
              className="saved-career-card"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <span>{career.field || "Career Field"}</span>
              <h2>{career.title}</h2>
              <p>{career.overview || "No overview has been added for this saved career."}</p>

              <div className="cc-chip-list">
                {(career.required_skills || []).slice(0, 4).map((skill) => (
                  <span key={skill}>{skill}</span>
                ))}
              </div>

              <div className="saved-actions">
                <Link className="cc-btn" to={`/career/${career.career_id}`} state={{ recommendation: career }}>
                  View Details
                </Link>
                <button
                  type="button"
                  className="cc-btn danger"
                  onClick={() => handleRemove(career.career_id)}
                  disabled={removingId === career.career_id}
                >
                  <FaTrashAlt />
                  {removingId === career.career_id ? "Removing..." : "Remove"}
                </button>
              </div>
            </motion.article>
          ))}
        </div>
      )}
    </StudentLayout>
  );
}
