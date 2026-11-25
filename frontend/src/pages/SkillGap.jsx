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
  const [selectedCareerId, setSelectedCareerId] = useState("");
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
          setSelectedCareerId(String(profileData?.selected_career_id || recommendationData[0]?.career_id || ""));
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

  const topRecommendation = recommendations.find((item) => String(item.career_id) === selectedCareerId)
    || recommendations.find((item) => item.career_id === profile?.selected_career_id)
    || recommendations[0]
    || null;
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
          <p>Choose any recommendation to view its own matched and missing skills.</p>
        </div>
        <Link className="cc-btn" to={`/resources?careerId=${topRecommendation.career_id}`}>
          Find Learning Resources
        </Link>
      </header>

      <section className="cc-card skill-gap-picker">
        <label htmlFor="career-skill-gap">Career recommendation</label>
        <select
          id="career-skill-gap"
          className="cc-select"
          value={selectedCareerId}
          onChange={(event) => setSelectedCareerId(event.target.value)}
        >
          {recommendations.map((recommendation) => (
            <option key={recommendation.career_id} value={recommendation.career_id}>
              {recommendation.title} — {Math.round(Number(recommendation.match_score) || 0)}% match
            </option>
          ))}
        </select>
      </section>

      <section className="cc-card">
        <h2>Career Readiness: {readiness}%</h2>
        <div className="progress">
          <div style={{ width: `${readiness}%` }} />
        </div>
      </section>

      <div className="cc-grid two">
        <section className="cc-card">
          <h2>Matched Skills for {topRecommendation.title}</h2>
          <div className="cc-chip-list">
            {(matchedSkills.length ? matchedSkills : ["No mapped skill matches yet"]).map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </section>

        <section className="cc-card">
          <h2>Skills To Improve for {topRecommendation.title}</h2>
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
