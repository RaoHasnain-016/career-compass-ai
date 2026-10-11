import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FaRobot,
  FaRoute,
  FaBookOpen,
  FaChartLine,
  FaArrowRight,
  FaBrain,
  FaGraduationCap,
  FaCheckCircle,
} from "react-icons/fa";
import "../styles/landing-page.css";

const featureCards = [
  {
    icon: <FaChartLine />,
    title: "Career Recommendations",
    description:
      "Personalized career suggestions based on academic profile, interests, skills, and future potential.",
  },
  {
    icon: <FaRoute />,
    title: "Career Roadmaps",
    description:
      "Step-by-step paths showing what to learn, what skills to build, and how to grow toward your selected career.",
  },
  {
    icon: <FaBookOpen />,
    title: "Learning Resources",
    description:
      "Free resources, courses, and video content selected according to your missing skills and career goal.",
  },
  {
    icon: <FaRobot />,
    title: "AI Chatbot",
    description:
      "A smart assistant that reads your profile, recommendations, roadmap, and resources to guide you properly.",
  },
];

const steps = [
  {
    number: "1",
    title: "Create Profile",
    description:
      "Add your academic level, subjects, interests, skills, marks, and learning preferences.",
  },
  {
    number: "2",
    title: "Get Recommendations",
    description:
      "The system analyzes your profile and generates ranked career recommendations with match scores.",
  },
  {
    number: "3",
    title: "Follow Roadmap",
    description:
      "Use a structured roadmap with learning resources, skill gaps, and video courses to move forward.",
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: (delay = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, delay, ease: "easeOut" },
  }),
};

function Landing() {
  return (
    <div className="landing-page">
      <header className="landing-navbar">
        <div className="landing-container navbar-inner">
          <Link to="/" className="brand">
            Career Compass AI
          </Link>

          <nav className="nav-links">
            <a href="#solutions">Solutions</a>
            <a href="#how-it-works">How It Works</a>
            <Link to="/roadmap">Roadmaps</Link>
            <Link to="/resources">Resources</Link>
          </nav>

          <div className="nav-actions">
            <Link to="/login" className="nav-signin">
              Sign In
            </Link>
            <Link to="/signup" className="nav-primary-btn">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="hero-section">
          <div className="landing-container hero-grid">
            <motion.div
              className="hero-content"
              initial="hidden"
              animate="show"
              variants={fadeUp}
            >
              <div className="ai-badge">
                <FaBrain />
                AI-Powered Student Career Platform
              </div>

              <motion.h1 custom={0.1} variants={fadeUp} className="hero-title">
                Shape Your Future With <span>AI-Powered</span> Career Guidance
              </motion.h1>

              <motion.p custom={0.2} variants={fadeUp} className="hero-text">
                Discover the right career path using academic profiling, skill
                gap analysis, smart recommendations, personalized roadmaps, free
                learning resources, video courses, and an AI career chatbot.
              </motion.p>

              <motion.div
                custom={0.3}
                variants={fadeUp}
                className="hero-actions"
              >
                <Link to="/signup" className="hero-btn primary">
                  Get Started <FaArrowRight />
                </Link>

                <Link to="/recommendations" className="hero-btn secondary">
                  Explore Careers
                </Link>
              </motion.div>

              <motion.div
                custom={0.4}
                variants={fadeUp}
                className="hero-trust"
              >
                <div className="avatar-group">
                  <img
                    src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=96&q=65"
                    alt="student"
                    loading="lazy"
                    decoding="async"
                  />
                  <img
                    src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=96&q=65"
                    alt="student"
                    loading="lazy"
                    decoding="async"
                  />
                  <img
                    src="https://images.unsplash.com/photo-1531123897727-8f129e1688ce?auto=format&fit=crop&w=96&q=65"
                    alt="student"
                    loading="lazy"
                    decoding="async"
                  />
                </div>
                <span>Trusted by students for smarter career planning</span>
              </motion.div>
            </motion.div>

            <motion.div
              className="hero-visual-wrap"
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
            >
              <div className="ai-glow ai-glow-1"></div>
              <div className="ai-glow ai-glow-2"></div>

              <div className="hero-image-card">
                <img
                  src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=800&q=70"
                  alt="students using laptops"
                  fetchPriority="high"
                  decoding="async"
                />

                <motion.div
                  className="floating-metric"
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 3, repeat: Infinity }}
                >
                  <span className="metric-label">AI Match Strength</span>
                  <strong>98% Data Scientist</strong>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        <section id="solutions" className="features-section">
          <div className="landing-container">
            <motion.div
              className="section-heading"
              initial={{ opacity: 0, y: 25 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <p className="section-kicker">Precision Career Intelligence</p>
              <h2>Powerful tools built for your career journey</h2>
              <p>
                Career Compass AI gives students a complete system: profile
                analysis, recommendations, roadmap planning, free learning
                resources, video courses, and AI guidance.
              </p>
            </motion.div>

            <div className="feature-grid">
              {featureCards.map((card, index) => (
                <motion.div
                  key={card.title}
                  className="feature-card"
                  initial={{ opacity: 0, y: 35 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  whileHover={{ y: -10, scale: 1.02 }}
                  transition={{ duration: 0.45, delay: index * 0.08 }}
                  viewport={{ once: true }}
                >
                  <div className="feature-icon">{card.icon}</div>
                  <h3>{card.title}</h3>
                  <p>{card.description}</p>
                  <div className="feature-hover-line"></div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="how-it-works" className="how-section">
          <div className="landing-container how-grid">
            <motion.div
              className="how-content"
              initial={{ opacity: 0, x: -25 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <p className="section-kicker">How It Works</p>
              <h2>Simple process, powerful outcomes</h2>

              <div className="steps-list">
                {steps.map((step, index) => (
                  <motion.div
                    key={step.number}
                    className="step-item"
                    initial={{ opacity: 0, y: 24 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.12 }}
                    viewport={{ once: true }}
                  >
                    <div className="step-number">{step.number}</div>
                    <div>
                      <h4>{step.title}</h4>
                      <p>{step.description}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              className="how-visual"
              initial={{ opacity: 0, x: 25 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <div className="dashboard-card">
                <div className="match-card">
                  <div className="match-top">
                    <div className="match-icon">
                      <FaRobot />
                    </div>
                    <div>
                      <span>Match Strength</span>
                      <strong>98% Data Scientist</strong>
                    </div>
                  </div>

                  <div className="progress-track">
                    <motion.div
                      className="progress-fill"
                      initial={{ width: 0 }}
                      whileInView={{ width: "98%" }}
                      transition={{ duration: 1.2, ease: "easeOut" }}
                      viewport={{ once: true }}
                    />
                  </div>
                </div>

                <div className="ai-dashboard-preview">
                  <div className="preview-topbar">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>

                  <div className="preview-content">
                    <div className="preview-chart">
                      <div style={{ height: "28%" }}></div>
                      <div style={{ height: "52%" }}></div>
                      <div style={{ height: "35%" }}></div>
                      <div style={{ height: "76%" }}></div>
                      <div style={{ height: "45%" }}></div>
                      <div style={{ height: "88%" }}></div>
                    </div>

                    <div className="preview-panel">
                      <div>
                        <FaCheckCircle />
                        <span>Skill Gap Detected</span>
                      </div>
                      <div>
                        <FaCheckCircle />
                        <span>Roadmap Generated</span>
                      </div>
                      <div>
                        <FaCheckCircle />
                        <span>Resources Matched</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <section className="cta-section">
          <div className="landing-container">
            <motion.div
              className="cta-card"
              initial={{ opacity: 0, scale: 0.96 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.55 }}
              viewport={{ once: true }}
            >
              <div className="cta-orb cta-orb-one"></div>
              <div className="cta-orb cta-orb-two"></div>

              <h2>Ready to find your path?</h2>
              <p>
                Start your profile, generate recommendations, follow your career
                roadmap, and get AI-powered guidance for your future.
              </p>

              <Link to="/signup" className="cta-btn">
                Get Started Now
              </Link>
            </motion.div>
          </div>
        </section>
      </main>

      <footer id="footer" className="landing-footer">
        <div className="landing-container footer-grid">
          <div>
            <h3>Career Compass AI</h3>
            <p>
              © 2024 Career Compass AI. Empowering the next generation of
              professionals.
            </p>
          </div>

          <div>
            <h4>Platform</h4>
            <Link to="/recommendations">Career Guide</Link>
            <Link to="/roadmap">Roadmaps</Link>
            <Link to="/dashboard">Dashboard</Link>
          </div>

          <div>
            <h4>Resources</h4>
            <Link to="/resources">Learning Resources</Link>
            <Link to="/chatbot">AI Chatbot</Link>
            <Link to="/saved-careers">Saved Careers</Link>
          </div>

          <div>
            <h4>Legal</h4>
            <Link to="/terms">Terms & Privacy</Link>
            <Link to="/contact">Contact Us</Link>
            <Link to="/about">About Project</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Landing;
