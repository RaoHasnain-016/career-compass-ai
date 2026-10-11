import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  FaBolt,
  FaBrain,
  FaCheckCircle,
  FaClock,
  FaHistory,
  FaLightbulb,
  FaPaperPlane,
  FaRobot,
  FaUserCircle,
} from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { askChatbot, getChatHistory } from "../services/chatbotService";
import "../styles/chatbot-page.css";

const suggestedQuestions = [
  {
    label: "Best career",
    text: "Which career is best for me based on my profile?",
    icon: <FaBrain />,
  },
  {
    label: "Skills first",
    text: "What skills should I improve first?",
    icon: <FaBolt />,
  },
  {
    label: "Roadmap",
    text: "Explain the roadmap for my top recommendation.",
    icon: <FaCheckCircle />,
  },
  {
    label: "Resources",
    text: "Suggest free resources for my missing skills.",
    icon: <FaLightbulb />,
  },
];

const messageVariants = {
  hidden: { opacity: 0, y: 14, scale: 0.98 },
  visible: { opacity: 1, y: 0, scale: 1 },
};

function historyToMessages(history) {
  return history.flatMap((item) => [
    {
      role: "user",
      text: item.question,
      id: `${item.message_id}-q`,
      createdAt: item.created_at,
    },
    {
      role: "assistant",
      text: item.response,
      id: `${item.message_id}-a`,
      createdAt: item.created_at,
    },
  ]);
}

function formatTime(value) {
  if (!value) return "";

  try {
    return new Intl.DateTimeFormat(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return "";
  }
}

function cleanMarkdownMarker(text) {
  return text.replace(/^\*\*/, "").replace(/\*\*$/, "").replace(/:$/, "").trim();
}

function isHeading(line) {
  return (
    /^\*\*[^*]+\*\*$/.test(line) ||
    /^[A-Z][A-Za-z0-9 /&-]{2,32}:$/.test(line)
  );
}

function isBullet(line) {
  return /^[-*]\s+/.test(line);
}

function isNumbered(line) {
  return /^\d+\.\s+/.test(line);
}

function renderInline(text) {
  const parts = String(text).split(/(\*\*[^*]+\*\*|https?:\/\/[^\s)]+)/g);

  return parts.map((part, index) => {
    if (!part) return null;

    if (/^\*\*[^*]+\*\*$/.test(part)) {
      return <strong key={`${part}-${index}`}>{cleanMarkdownMarker(part)}</strong>;
    }

    if (/^https?:\/\//.test(part)) {
      return (
        <a key={`${part}-${index}`} href={part} target="_blank" rel="noreferrer">
          {part}
        </a>
      );
    }

    return <span key={`${part}-${index}`}>{part}</span>;
  });
}

function renderMessageContent(text) {
  const lines = String(text || "")
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) {
    return <p>I could not generate a response.</p>;
  }

  const content = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (isHeading(line)) {
      content.push(
        <h3 key={`heading-${index}`} dir="auto">{cleanMarkdownMarker(line)}</h3>
      );
      index += 1;
      continue;
    }

    if (isBullet(line)) {
      const items = [];

      while (index < lines.length && isBullet(lines[index])) {
        items.push(lines[index].replace(/^[-*]\s+/, ""));
        index += 1;
      }

      content.push(
        <ul key={`list-${index}`} dir="auto">
          {items.map((item, itemIndex) => (
            <li key={`${item}-${itemIndex}`}>{renderInline(item)}</li>
          ))}
        </ul>
      );
      continue;
    }

    if (isNumbered(line)) {
      const items = [];

      while (index < lines.length && isNumbered(lines[index])) {
        items.push(lines[index].replace(/^\d+\.\s+/, ""));
        index += 1;
      }

      content.push(
        <ol key={`steps-${index}`} dir="auto">
          {items.map((item, itemIndex) => (
            <li key={`${item}-${itemIndex}`}>{renderInline(item)}</li>
          ))}
        </ol>
      );
      continue;
    }

    const paragraphLines = [];

    while (
      index < lines.length &&
      !isHeading(lines[index]) &&
      !isBullet(lines[index]) &&
      !isNumbered(lines[index])
    ) {
      paragraphLines.push(lines[index]);
      index += 1;
    }

    content.push(
      <p key={`paragraph-${index}`} dir="auto">
        {paragraphLines.map((paragraphLine, lineIndex) => (
          <span key={`${paragraphLine}-${lineIndex}`}>
            {renderInline(paragraphLine)}
            {lineIndex < paragraphLines.length - 1 && <br />}
          </span>
        ))}
      </p>
    );
  }

  return content;
}

export default function Chatbot() {
  const location = useLocation();
  const careerId = location.state?.careerId || "";
  const careerTitle = location.state?.careerTitle || "";
  const bottomRef = useRef(null);

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text:
        "What would you like help with: choosing a career, learning a skill, or planning your next step? Ask in your preferred language.",
      id: "welcome",
      createdAt: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadHistory() {
      try {
        const history = await getChatHistory();
        if (active && history.length) {
          setMessages(historyToMessages(history));
        }
      } catch (error) {
        console.error(error);
      } finally {
        if (active) setLoadingHistory(false);
      }
    }

    loadHistory();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const sendMessage = async (text = input) => {
    const trimmed = text.trim();
    if (!trimmed || sending || loadingHistory) return;

    const startedAt = performance.now();
    const userMessage = {
      role: "user",
      text: trimmed,
      id: `user-${Date.now()}`,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);
    setError("");

    try {
      const response = await askChatbot(trimmed, { careerId });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            response?.response ||
            response?.message ||
            "I could not generate a response.",
          id: response?.message_id || `assistant-${Date.now()}`,
          createdAt: new Date().toISOString(),
          responseTime: `${Math.max(
            1,
            Math.round((performance.now() - startedAt) / 1000)
          )}s`,
        },
      ]);
    } catch (error) {
      console.error(error);
      const errorMessage = error.message || "AI response could not be loaded. Please try again.";
      setError(errorMessage);
      setInput((current) => current || trimmed);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: errorMessage,
          id: `assistant-error-${Date.now()}`,
          createdAt: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <StudentLayout className="chatbot-page">
      <header className="chat-hero">
        <motion.div
          className="chat-bot-mark"
          initial={{ rotate: -8, scale: 0.92 }}
          animate={{ rotate: 0, scale: 1 }}
          transition={{ type: "spring", stiffness: 180, damping: 14 }}
        >
          <FaRobot />
          <span></span>
        </motion.div>

        <div className="chat-hero-copy">
          <span className="chat-eyebrow">
            <FaBolt />
            Fast mode
          </span>
          <h1>AI Career Assistant</h1>
          <p>
            {careerTitle
              ? `Focused on ${careerTitle} with your roadmap context.`
              : "Using your profile, recommendations, saved careers, and roadmap data."}
          </p>
        </div>

        <div className="chat-hero-actions">
          <div className="chat-status-pill">
            <span></span>
            Online
          </div>
          <Link className="chat-history-link" to="/chat-history">
            <FaHistory />
            History
          </Link>
        </div>
      </header>

      {error && <div className="chat-error">{error}</div>}

      <div className="chat-layout">
        <section className="chat-panel">
          <div className="chat-history">
            {loadingHistory && (
              <div className="chat-system-note">
                <FaClock />
                Loading previous conversations...
              </div>
            )}

            <AnimatePresence initial={false}>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  className={`chat-message ${
                    message.role === "user" ? "user" : "assistant"
                  }`}
                  variants={messageVariants}
                  initial="hidden"
                  animate="visible"
                  exit="hidden"
                  transition={{ duration: 0.2 }}
                  layout
                >
                  <span className="chat-avatar">
                    {message.role === "user" ? <FaUserCircle /> : <FaRobot />}
                  </span>

                  <div className="chat-bubble">
                    <div className="chat-meta">
                      <strong>
                        {message.role === "user" ? "You" : "Career Compass AI"}
                      </strong>
                      <small>
                        {message.responseTime || formatTime(message.createdAt)}
                      </small>
                    </div>

                    <div className="chat-content" dir="auto">
                      {renderMessageContent(message.text)}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {sending && (
              <motion.div
                className="chat-message assistant"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <span className="chat-avatar">
                  <FaRobot />
                </span>
                <div className="chat-bubble typing-bubble">
                  <div className="chat-meta">
                    <strong>Career Compass AI</strong>
                    <small>replying</small>
                  </div>
                  <div className="typing-dots" aria-label="Assistant is typing">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={bottomRef}></div>
          </div>

          <form
            className="chat-input-row"
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage();
            }}
          >
            <textarea
              dir="auto"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about careers in your preferred language..."
              rows={1}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing &&
                  event.nativeEvent.keyCode !== 229
                ) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
            />
            <button type="submit" disabled={loadingHistory || sending || !input.trim()} title="Send message">
              <FaPaperPlane />
            </button>
          </form>
        </section>

        <aside className="chat-suggestions">
          <div className="chat-side-section">
            <h2>Suggested Questions</h2>
            {careerTitle && <p>Focused on: {careerTitle}</p>}
            <div className="suggestion-list">
              {suggestedQuestions.map((question) => (
                <button
                  key={question.text}
                  type="button"
                  onClick={() => sendMessage(question.text)}
                  disabled={loadingHistory || sending}
                >
                  <span>{question.icon}</span>
                  <div>
                    <strong>{question.label}</strong>
                    <small>{question.text}</small>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="chat-side-section compact">
            <h2>Response Style</h2>
            <div className="format-list">
              <span>
                <FaCheckCircle />
                Short answer
              </span>
              <span>
                <FaCheckCircle />
                Action steps
              </span>
              <span>
                <FaCheckCircle />
                Skill focus
              </span>
            </div>
          </div>
        </aside>
      </div>
    </StudentLayout>
  );
}
