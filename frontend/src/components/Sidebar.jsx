import { useId, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  FaBars,
  FaBell,
  FaBookOpen,
  FaBookmark,
  FaChartLine,
  FaCog,
  FaCompass,
  FaHome,
  FaGraduationCap,
  FaQuestionCircle,
  FaRobot,
  FaRoute,
  FaTimes,
  FaUser,
} from "react-icons/fa";

const items = [
  ["/dashboard", "Dashboard", <FaHome />],
  ["/notifications", "Notifications", <FaBell />],
  ["/profile-setup", "Profile Setup", <FaCompass />],
  ["/recommendations", "Recommendations", <FaChartLine />],
  ["/universities", "Study Options", <FaGraduationCap />],
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
  const navigationId = useId();
  const menuButton = useRef(null);
  const [openLocation, setOpenLocation] = useState(null);
  const isOpen = openLocation === location.key;

  function closeOnEscape(event) {
    if (event.key !== "Escape" || !isOpen) return;
    setOpenLocation(null);
    menuButton.current?.focus();
  }

  return (
    <aside className="student-sidebar" onKeyDown={closeOnEscape}>
      <div className="student-sidebar-heading">
        <Link to="/" className="student-brand" onClick={() => setOpenLocation(null)}>
          <span aria-hidden="true"><FaCompass /></span>
          <div>
            <strong>Career Compass AI</strong>
            <small>Student Workspace</small>
          </div>
        </Link>
        <button
          ref={menuButton}
          type="button"
          className="student-menu-toggle"
          aria-expanded={isOpen}
          aria-controls={navigationId}
          onClick={() => setOpenLocation(isOpen ? null : location.key)}
        >
          {isOpen ? <FaTimes aria-hidden="true" /> : <FaBars aria-hidden="true" />}
          <span>Menu</span>
        </button>
      </div>

      <nav id={navigationId} className="student-nav" aria-label="Student navigation" data-open={isOpen}>
        {items.map(([to, label, icon]) => (
          <Link
            key={to}
            to={to}
            className={location.pathname === to ? "active" : ""}
            aria-current={location.pathname === to ? "page" : undefined}
            onClick={() => setOpenLocation(null)}
          >
            {icon}
            <span>{label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
