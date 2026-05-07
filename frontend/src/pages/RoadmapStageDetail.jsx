import { Link, useLocation } from "react-router-dom";
import { FaRoute } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";

function asArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") return value.split(",").map((item) => item.trim()).filter(Boolean);
  return [];
}

export default function RoadmapStageDetail() {
  const location = useLocation();
  const stage = location.state?.stage || null;

  if (!stage) {
    return (
      <StudentLayout>
        <div className="cc-empty">
          <FaRoute />
          <h2>Roadmap stage unavailable</h2>
          <p>Open a roadmap from a selected recommendation to view stage details.</p>
          <Link className="cc-btn" to="/roadmap">
            Back to Roadmap
          </Link>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout>
      <header className="cc-page-header">
        <div>
          <h1>{stage.title}</h1>
          <p>{stage.description || "Stage details for your selected career roadmap."}</p>
        </div>
      </header>

      <div className="cc-grid two">
        <section className="cc-card">
          <h2>Required Skills</h2>
          <div className="cc-chip-list">
            {asArray(stage.required_skills).map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </section>

        <section className="cc-card">
          <h2>Suggested Resources</h2>
          <div className="cc-chip-list">
            {asArray(stage.suggested_resources).map((resource) => (
              <span key={resource}>{resource}</span>
            ))}
          </div>
        </section>
      </div>
    </StudentLayout>
  );
}
