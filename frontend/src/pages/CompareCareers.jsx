import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FaBalanceScale, FaRobot } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { getMyRecommendations } from "../services/recommendationService";

function asArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") return value.split(",").map((item) => item.trim()).filter(Boolean);
  return [];
}

export default function CompareCareers() {
  const [careers, setCareers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadCareers() {
      try {
        setLoading(true);
        setError("");
        const data = await getMyRecommendations();
        if (active) setCareers(data.slice(0, 3));
      } catch (error) {
        console.error(error);
        if (active) setError(error.message || "Career comparison data could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadCareers();

    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <StudentLayout>
        <div className="cc-loading">
          <div className="cc-loader">
            <FaBalanceScale />
          </div>
          <h2>Preparing comparison...</h2>
          <p>Loading your top recommended careers.</p>
        </div>
      </StudentLayout>
    );
  }

  if (careers.length < 2) {
    return (
      <StudentLayout>
        <div className="cc-empty">
          <FaRobot />
          <h2>Not enough careers to compare</h2>
          <p>{error || "Generate recommendations to compare your strongest career matches."}</p>
          <Link className="cc-btn" to="/recommendations">Open Recommendations</Link>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout>
      <header className="cc-page-header">
        <div>
          <h1>Compare Careers</h1>
          <p>Compare your top AI recommendations side by side.</p>
        </div>
      </header>

      <table className="table">
        <thead>
          <tr>
            <th>Criteria</th>
            {careers.map((career) => (
              <th key={career.career_id}>{career.title}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Match Score</td>
            {careers.map((career) => (
              <td key={career.career_id}>{Math.round(Number(career.match_score || 0))}%</td>
            ))}
          </tr>
          <tr>
            <td>Field</td>
            {careers.map((career) => (
              <td key={career.career_id}>{career.field || "N/A"}</td>
            ))}
          </tr>
          <tr>
            <td>Difficulty</td>
            {careers.map((career) => (
              <td key={career.career_id}>{career.difficulty_level || "N/A"}</td>
            ))}
          </tr>
          <tr>
            <td>Matched Skills</td>
            {careers.map((career) => (
              <td key={career.career_id}>{asArray(career.matched_skills).join(", ") || "N/A"}</td>
            ))}
          </tr>
          <tr>
            <td>Missing Skills</td>
            {careers.map((career) => (
              <td key={career.career_id}>{asArray(career.missing_skills).join(", ") || "No major gaps"}</td>
            ))}
          </tr>
          <tr>
            <td>Future Scope</td>
            {careers.map((career) => (
              <td key={career.career_id}>{career.future_scope || "N/A"}</td>
            ))}
          </tr>
        </tbody>
      </table>
    </StudentLayout>
  );
}
