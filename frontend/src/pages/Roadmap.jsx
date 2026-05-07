import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { FaCheck, FaExclamationTriangle, FaRobot, FaRoute } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { getRoadmap, getTopRecommendedCareerId } from "../services/roadmapService";
import "../styles/roadmap-page.css";

function asArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") return value.split(",").map((item) => item.trim()).filter(Boolean);
  return [];
}

export default function Roadmap() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const requestedCareerId = searchParams.get("careerId") || location.state?.careerId || "";

  const [careerId, setCareerId] = useState(requestedCareerId);
  const [career, setCareer] = useState(location.state?.careerTitle ? { title: location.state.careerTitle } : null);
  const [stages, setStages] = useState([]);
  const [completedStages, setCompletedStages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadRoadmap() {
      try {
        setLoading(true);
        setError("");

        const resolvedCareerId = requestedCareerId || (await getTopRecommendedCareerId());

        if (!resolvedCareerId) {
          if (active) {
            setCareerId("");
            setStages([]);
          }
          return;
        }

        const response = await getRoadmap(resolvedCareerId);

        if (active) {
          setCareerId(resolvedCareerId);
          setCareer(response.career || career);
          setStages(response.roadmap || []);
        }
      } catch (error) {
        console.error(error);

        if (active) {
          setError(error.message || "Roadmap could not be loaded.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadRoadmap();

    return () => {
      active = false;
    };
  }, [requestedCareerId]);

  const progress = useMemo(() => {
    if (!stages.length) return 0;
    return Math.round((completedStages.length / stages.length) * 100);
  }, [completedStages, stages]);

  const toggleStage = (stageId) => {
    setCompletedStages((prev) =>
      prev.includes(stageId) ? prev.filter((item) => item !== stageId) : [...prev, stageId]
    );
  };

  if (loading) {
    return (
      <StudentLayout>
        <div className="cc-loading">
          <div className="cc-loader">
            <FaRoute />
          </div>
          <h2>Opening your roadmap...</h2>
          <p>Loading the stages for your selected or top recommended career.</p>
        </div>
      </StudentLayout>
    );
  }

  if (error) {
    return (
      <StudentLayout>
        <div className="cc-error">
          <FaExclamationTriangle />
          <h2>Roadmap unavailable</h2>
          <p>{error}</p>
          <Link className="cc-btn" to="/recommendations">
            Open Recommendations
          </Link>
        </div>
      </StudentLayout>
    );
  }

  if (!careerId || stages.length === 0) {
    return (
      <StudentLayout>
        <div className="cc-empty">
          <FaRobot />
          <h2>No roadmap selected</h2>
          <p>Generate recommendations first, then open a roadmap for a specific career.</p>
          <div className="cc-actions">
            <Link className="cc-btn" to="/recommendations">
              Open Recommendations
            </Link>
            <Link className="cc-btn secondary" to="/profile-setup">
              Complete Profile
            </Link>
          </div>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout className="roadmap-page">
      <header className="cc-page-header">
        <div>
          <h1>Your Career Roadmap</h1>
          <p>Selected career: {career?.title || "Recommended Career"}</p>
        </div>
        <Link className="cc-btn secondary" to="/recommendations">
          Change Career
        </Link>
      </header>

      <section className="roadmap-progress-card">
        <div>
          <span>Roadmap Progress</span>
          <strong>{progress}%</strong>
        </div>
        <div className="roadmap-progress-track">
          <span style={{ width: `${progress}%` }}></span>
        </div>
      </section>

      <div className="roadmap-stage-list">
        {stages.map((stage, index) => {
          const stageId = stage.stage_id || `${stage.title}-${index}`;
          const completed = completedStages.includes(stageId);

          return (
            <motion.article
              key={stageId}
              className={`roadmap-stage-card ${completed ? "completed" : ""}`}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <button type="button" onClick={() => toggleStage(stageId)}>
                {completed ? <FaCheck /> : index + 1}
              </button>

              <div>
                <span>Stage {stage.stage_order || index + 1}</span>
                <h2>{stage.title}</h2>
                <p>{stage.description || "No description has been added for this roadmap stage."}</p>

                <div className="roadmap-stage-grid">
                  <div>
                    <h3>Skills</h3>
                    <div className="cc-chip-list">
                      {asArray(stage.required_skills).map((skill) => (
                        <span key={skill}>{skill}</span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3>Resources</h3>
                    <div className="cc-chip-list">
                      {asArray(stage.suggested_resources).map((resource) => (
                        <span key={resource}>{resource}</span>
                      ))}
                    </div>
                  </div>
                </div>

                <Link className="cc-btn secondary" to="/roadmap-stage" state={{ stage }}>
                  View Stage Detail
                </Link>
              </div>
            </motion.article>
          );
        })}
      </div>
    </StudentLayout>
  );
}
