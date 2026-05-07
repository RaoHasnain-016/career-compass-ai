import { Link, useLocation } from "react-router-dom";
import {
  FaBookOpen,
  FaBookmark,
  FaChartLine,
  FaCog,
  FaCompass,
  FaHome,
  FaQuestionCircle,
  FaRobot,
  FaRoute,
  FaUser,
} from "react-icons/fa";

const items = [
  ["/dashboard", "Dashboard", <FaHome />],
  ["/profile-setup", "Profile Setup", <FaCompass />],
  ["/recommendations", "Recommendations", <FaChartLine />],
  ["/roadmap", "Roadmap", <FaRoute />],
  ["/skill-gap", "Skill Gap", <FaChartLine />],
  ["/resources", "Resources", <FaBookOpen />],
  ["/chatbot", "AI Chatbot", <FaRobot />],
  ["/saved-careers", "Saved Careers", <FaBookmark />],
  ["/profile", "Profile", <FaUser />],
  ["/settings", "Settings", <FaCog />],
  ["/help", "Help", <FaQuestionCircle />],
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="student-sidebar">
      <Link to="/" className="student-brand">
        <span>
          <FaCompass />
        </span>
        <div>
          <strong>Career Compass AI</strong>
          <small>Student Workspace</small>
        </div>
      </Link>

      <nav className="student-nav">
        {items.map(([to, label, icon]) => (
          <Link
            key={to}
            to={to}
            className={location.pathname === to ? "active" : ""}
          >
            {icon}
            <span>{label}</span>
          </Link>
        ))}
      </nav>

      <Link to="/admin" className="student-admin-link">
        Admin Panel
      </Link>
    </aside>
  );
}
