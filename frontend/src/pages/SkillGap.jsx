import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FaChartLine, FaRobot } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { getMyRecommendations } from "../services/recommendationService";
import { getStudentProfile } from "../services/profileService";

function asArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") return value.split(",").map((item) => item.trim()).filter(Boolean);
  return [];
}

export default function SkillGap() {
  const [profile, setProfile] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadData() {
      try {
        setLoading(true);
        setError("");
        const [profileData, recommendationData] = await Promise.all([
          getStudentProfile().catch(() => null),
          getMyRecommendations(),
        ]);

        if (active) {
          setProfile(profileData);
          setRecommendations(recommendationData);
        }
      } catch (error) {
        console.error(error);
        if (active) setError(error.message || "Skill gap data could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadData();

    return () => {
      active = false;
    };
  }, []);

  const topRecommendation = recommendations.find((item) => item.career_id === profile?.selected_career_id) || recommendations[0] || null;
  const currentSkills = asArray(profile?.skills);
  const matchedSkills = asArray(topRecommendation?.matched_skills);
  const missingSkills = asArray(topRecommendation?.missing_skills);
  const readiness = useMemo(() => {
    const total = matchedSkills.length + missingSkills.length;
    if (!total) return 0;
    return Math.round((matchedSkills.length / total) * 100);
  }, [matchedSkills.length, missingSkills.length]);

  if (loading) {
    return (
      <StudentLayout>
        <div className="cc-loading">
          <div className="cc-loader">
            <FaChartLine />
          </div>
          <h2>Analyzing skill gaps...</h2>
          <p>Comparing your profile skills with your top recommendation.</p>
        </div>
      </StudentLayout>
    );
  }

  if (!topRecommendation) {
    return (
      <StudentLayout>
        <div className="cc-empty">
          <FaRobot />
          <h2>No recommendation data</h2>
          <p>{error || "Generate recommendations to see a personalized skill gap analysis."}</p>
          <Link className="cc-btn" to="/recommendations">Open Recommendations</Link>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout>
      <header className="cc-page-header">
        <div>
          <h1>Skill Gap Analysis</h1>
          <p>Focused on your top recommendation: {topRecommendation.title}.</p>
        </div>
        <Link className="cc-btn" to={`/resources?careerId=${topRecommendation.career_id}`}>
          Find Learning Resources
        </Link>
      </header>

      <section className="cc-card">
        <h2>Career Readiness: {readiness}%</h2>
        <div className="progress">
          <div style={{ width: `${readiness}%` }} />
        </div>
      </section>

      <div className="cc-grid two">
        <section className="cc-card">
          <h2>Your Current Skills</h2>
          <div className="cc-chip-list">
            {(currentSkills.length ? currentSkills : matchedSkills).map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </section>

        <section className="cc-card">
          <h2>Skills To Improve</h2>
          <div className="cc-chip-list weak">
            {(missingSkills.length ? missingSkills : ["No major skill gaps found"]).map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </section>
      </div>
    </StudentLayout>
  );
}
