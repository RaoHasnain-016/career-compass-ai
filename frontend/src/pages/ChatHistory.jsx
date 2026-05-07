import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FaComments, FaRobot } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { getChatHistory } from "../services/chatbotService";

export default function ChatHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadHistory() {
      try {
        setLoading(true);
        setError("");
        const data = await getChatHistory();
        if (active) setHistory(data);
      } catch (error) {
        console.error(error);
        if (active) setError(error.message || "Chat history could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadHistory();

    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <StudentLayout>
        <div className="cc-loading">
          <div className="cc-loader">
            <FaComments />
          </div>
          <h2>Loading chat history...</h2>
          <p>Fetching your previous AI career guidance messages.</p>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout>
      <header className="cc-page-header">
        <div>
          <h1>Chat History</h1>
          <p>Review previous questions and AI responses tied to your account.</p>
        </div>
        <Link className="cc-btn" to="/chatbot">
          Open Chatbot
        </Link>
      </header>

      {error && <div className="cc-error"><p>{error}</p></div>}

      {history.length === 0 ? (
        <div className="cc-empty">
          <FaRobot />
          <h2>No chat history yet</h2>
          <p>Start a conversation with the AI assistant to build your history.</p>
          <Link className="cc-btn" to="/chatbot">Ask AI</Link>
        </div>
      ) : (
        <div className="cc-grid">
          {history.map((item) => (
            <article className="cc-card" key={item.message_id}>
              <h2>{item.question}</h2>
              <p>{item.response}</p>
            </article>
          ))}
        </div>
      )}
    </StudentLayout>
  );
}
