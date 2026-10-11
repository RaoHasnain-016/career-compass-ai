import { Link, useLocation } from "react-router-dom";
import { FaRobot } from "react-icons/fa";
import "../styles/landing-page.css";

function FloatingChatbotButton() {
  const location = useLocation();

  if (location.pathname === "/chatbot") {
    return null;
  }

  return (
    <div className="floating-chatbot-wrapper">
      <Link to="/chatbot" className="floating-chatbot-btn">
        <FaRobot aria-hidden="true" />
        <span className="sr-only">Open AI Chatbot</span>
      </Link>
    </div>
  );
}

export default FloatingChatbotButton;
