import { motion } from "framer-motion";
import { FaBrain, FaChartLine, FaRoute } from "react-icons/fa";
import Navbar from "../components/Navbar";
import "../styles/static-page.css";

const pillars = [
  ["AI Recommendations", "Profile-aware matching across careers, subjects, interests, and skills.", <FaBrain />],
  ["Career Roadmaps", "Structured stages that show how students can progress toward a selected path.", <FaRoute />],
  ["Skill Gap Analytics", "Matched and missing skills drive resource and video recommendations.", <FaChartLine />],
];

export default function AboutProject() {
  return (
    <>
      <Navbar />
      <main className="public-static-page">
        <section className="public-static-hero">
          <span>About the Project</span>
          <h1>Career Compass AI</h1>
          <p>
            A React, FastAPI, PostgreSQL, and Firebase powered career guidance
            platform built to help students make clearer academic and career decisions.
          </p>
        </section>

        <section className="public-static-card">
          <h2>What it does</h2>
          <p>
            The system authenticates users with Firebase, stores per-user student profiles,
            generates backend recommendations, and connects each career path to roadmaps,
            resources, saved careers, and AI chatbot guidance.
          </p>
        </section>

        <section className="public-pillar-grid">
          {pillars.map(([title, description, icon], index) => (
            <motion.article
              key={title}
              className="public-pillar-card"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08 }}
            >
              {icon}
              <h2>{title}</h2>
              <p>{description}</p>
            </motion.article>
          ))}
        </section>
      </main>
    </>
  );
}
