import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { FaRobot } from "react-icons/fa";
import "../styles/landing-page.css";

function FloatingChatbotButton() {
  const location = useLocation();

  if (location.pathname === "/chatbot") {
    return null;
  }

  return (
    <motion.div
      className="floating-chatbot-wrapper"
      initial={{ opacity: 0, scale: 0.7, y: 40 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.45 }}
    >
      <Link to="/chatbot" className="floating-chatbot-btn">
        <span className="chatbot-ping"></span>
        <FaRobot />
        <span>AI Chatbot</span>
      </Link>
    </motion.div>
  );
}

export default FloatingChatbotButton;