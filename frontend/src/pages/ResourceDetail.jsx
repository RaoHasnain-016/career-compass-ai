import { Link, useLocation, useParams } from "react-router-dom";
import { FaBookOpen, FaExternalLinkAlt } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";

export default function ResourceDetail() {
  const { id } = useParams();
  const location = useLocation();
  const resource = location.state?.resource || null;

  if (!resource) {
    return (
      <StudentLayout>
        <div className="cc-empty">
          <FaBookOpen />
          <h2>Resource details unavailable</h2>
          <p>Open resources from the recommended learning resources page.</p>
          <Link className="cc-btn" to="/resources">
            Back to Resources
          </Link>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout>
      <header className="cc-page-header">
        <div>
          <h1>{resource.title || `Resource ${id}`}</h1>
          <p>{resource.description || "Learning material selected for your career skill gaps."}</p>
        </div>
        <a className="cc-btn" href={resource.url || resource.video_url || "#"} target="_blank" rel="noreferrer">
          <FaExternalLinkAlt />
          Open Resource
        </a>
      </header>

      <section className="cc-card">
        <div className="cc-chip-list">
          <span>{resource.platform || resource.source || "Learning Source"}</span>
          <span>{resource.skill || "Career Skill"}</span>
          <span>{resource.difficulty || "Beginner"}</span>
          {resource.is_free !== false && <span>Free</span>}
        </div>
      </section>
    </StudentLayout>
  );
}
