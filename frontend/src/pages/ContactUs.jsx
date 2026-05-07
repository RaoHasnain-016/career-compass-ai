import { useState } from "react";
import { motion } from "framer-motion";
import { FaEnvelope, FaMapMarkerAlt, FaPaperPlane } from "react-icons/fa";
import Navbar from "../components/Navbar";
import "../styles/static-page.css";

export default function ContactUs() {
  const [submitted, setSubmitted] = useState(false);

  return (
    <>
      <Navbar />
      <main className="public-static-page">
        <section className="public-static-hero">
          <span>Career Compass AI Support</span>
          <h1>Contact Us</h1>
          <p>Reach out for project questions, evaluator feedback, or guidance workflow support.</p>
        </section>

        <section className="public-static-grid">
          <motion.form
            className="static-form-card"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            onSubmit={(event) => {
              event.preventDefault();
              setSubmitted(true);
            }}
          >
            <input className="cc-input" placeholder="Name" required />
            <input className="cc-input" type="email" placeholder="Email" required />
            <input className="cc-input" placeholder="Subject" required />
            <textarea className="cc-textarea" placeholder="Message" required />
            <button className="cc-btn" type="submit">
              <FaPaperPlane />
              Submit
            </button>
            {submitted && <p className="static-success">Message prepared successfully.</p>}
          </motion.form>

          <aside className="static-info-card">
            <div>
              <FaEnvelope />
              <h2>Email</h2>
              <p>support@careercompass.ai</p>
            </div>
            <div>
              <FaMapMarkerAlt />
              <h2>Project</h2>
              <p>AI career guidance platform for students.</p>
            </div>
          </aside>
        </section>
      </main>
    </>
  );
}
