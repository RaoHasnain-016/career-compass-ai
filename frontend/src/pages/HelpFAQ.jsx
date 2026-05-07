import { useMemo, useState } from "react";
import { FaQuestionCircle, FaSearch } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import "../styles/static-page.css";

const faqs = [
  {
    question: "How does career recommendation work?",
    answer:
      "Career Compass AI compares your academic profile, subjects, interests, and skills with active career records from the backend.",
  },
  {
    question: "Why do I need to complete my profile?",
    answer:
      "Profile data lets the backend generate user-specific recommendations, missing skills, roadmaps, and resource suggestions.",
  },
  {
    question: "Are learning resources free?",
    answer:
      "The resource engine prioritizes free or freely accessible courses, articles, and YouTube videos for missing skills.",
  },
  {
    question: "Can I regenerate recommendations?",
    answer:
      "Yes. Update your profile any time, then regenerate recommendations to refresh dashboard and recommendation results.",
  },
];

export default function HelpFAQ() {
  const [query, setQuery] = useState("");

  const filteredFaqs = useMemo(() => {
    const value = query.trim().toLowerCase();
    if (!value) return faqs;
    return faqs.filter((item) =>
      `${item.question} ${item.answer}`.toLowerCase().includes(value)
    );
  }, [query]);

  return (
    <StudentLayout className="static-student-page">
      <header className="cc-page-header">
        <div>
          <h1>Help & FAQ</h1>
          <p>Answers for profile setup, recommendations, roadmaps, resources, and AI chat.</p>
        </div>
      </header>

      <div className="static-search">
        <FaSearch />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search help topics..." />
      </div>

      <div className="faq-list">
        {filteredFaqs.map((item) => (
          <article className="cc-card" key={item.question}>
            <h2>
              <FaQuestionCircle />
              {item.question}
            </h2>
            <p>{item.answer}</p>
          </article>
        ))}
      </div>
    </StudentLayout>
  );
}
