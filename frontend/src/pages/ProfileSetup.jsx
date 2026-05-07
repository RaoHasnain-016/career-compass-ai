import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  FaArrowLeft,
  FaArrowRight,
  FaBookOpen,
  FaBrain,
  FaCheck,
  FaCompass,
  FaGraduationCap,
  FaLightbulb,
  FaPlus,
  FaRobot,
  FaSave,
  FaSearch,
  FaTools,
} from "react-icons/fa";
import {
  generateRecommendations,
  getStudentProfile,
  saveStudentProfile,
} from "../services/profileService";
import "../styles/profile-setup.css";

const DRAFT_KEY = "careerCompassProfileDraft";

const subjects = [
  "Computer Science",
  "Mathematics",
  "Biology",
  "Chemistry",
  "Physics",
  "English",
  "Business Studies",
  "Economics",
  "Arts",
  "Statistics",
];

const interestOptions = [
  "Technology",
  "Medical",
  "Business",
  "Teaching",
  "Design",
  "Data",
  "Research",
  "Helping People",
  "Creativity",
  "Management",
  "Problem Solving",
  "Communication",
];

const skillOptions = [
  "Programming",
  "Database",
  "Web Development",
  "Communication",
  "Leadership",
  "Problem Solving",
  "Excel",
  "Python",
  "SQL",
  "Design",
  "Research",
  "Presentation",
  "Critical Thinking",
  "Creativity",
];

const learningOptions = [
  "Video-based learning",
  "Reading documentation",
  "Project-based learning",
  "Practice exercises",
  "Mentor-guided learning",
  "Short courses",
];

const steps = [
  { id: 1, title: "Academic Info", icon: <FaGraduationCap /> },
  { id: 2, title: "Subjects", icon: <FaBookOpen /> },
  { id: 3, title: "Interests", icon: <FaBrain /> },
  { id: 4, title: "Skills", icon: <FaTools /> },
  { id: 5, title: "Learning Preferences", icon: <FaLightbulb /> },
  { id: 6, title: "Review", icon: <FaCheck /> },
];

const initialForm = {
  age: "",
  academic_level: "",
  class_degree: "",
  marks_cgpa: "",
  education_stream: "",
  current_institution: "",
  favorite_subjects: [],
  weak_subjects: [],
  interests: [],
  skills: [],
  study_preference: "",
  weekly_study_hours: "",
  preferred_language: "",
  career_goal_timeline: "",
};

function safeArray(value) {
  if (!value) return [];

  if (Array.isArray(value)) return value;

  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

function toggleValue(list, value) {
  if (list.includes(value)) {
    return list.filter((item) => item !== value);
  }

  return [...list, value];
}

function parseStudyPreference(value = "") {
  const parts = value.split("|").map((item) => item.trim());

  const parsed = {
    study_preference: parts[0] || "",
    weekly_study_hours: "",
    preferred_language: "",
    career_goal_timeline: "",
    education_stream: "",
    current_institution: "",
  };

  parts.slice(1).forEach((part) => {
    const lower = part.toLowerCase();

    if (lower.startsWith("weekly study hours:")) {
      parsed.weekly_study_hours = part.replace(/weekly study hours:/i, "").trim();
    }

    if (lower.startsWith("preferred language:")) {
      parsed.preferred_language = part.replace(/preferred language:/i, "").trim();
    }

    if (lower.startsWith("career goal timeline:")) {
      parsed.career_goal_timeline = part
        .replace(/career goal timeline:/i, "")
        .trim();
    }

    if (lower.startsWith("education stream:")) {
      parsed.education_stream = part.replace(/education stream:/i, "").trim();
    }

    if (lower.startsWith("current institution:")) {
      parsed.current_institution = part
        .replace(/current institution:/i, "")
        .trim();
    }
  });

  return parsed;
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveDraft(form) {
  localStorage.setItem(
    DRAFT_KEY,
    JSON.stringify({
      ...form,
      last_saved_at: new Date().toISOString(),
    })
  );
}

function ProfileSetup() {
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [highestStep, setHighestStep] = useState(1);
  const [form, setForm] = useState(initialForm);
  const [customSkill, setCustomSkill] = useState("");
  const [skillSearch, setSkillSearch] = useState("");
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [saving, setSaving] = useState(false);
  const [autoSaving, setAutoSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [draftLoaded, setDraftLoaded] = useState(false);

  const completion = useMemo(() => {
    const checks = [
      Boolean(form.age),
      Boolean(form.academic_level),
      Boolean(form.class_degree),
      Boolean(form.marks_cgpa),
      Boolean(form.education_stream),
      Boolean(form.current_institution),
      form.favorite_subjects.length > 0,
      form.weak_subjects.length > 0,
      form.interests.length > 0,
      form.skills.length > 0,
      Boolean(form.study_preference),
      Boolean(form.weekly_study_hours),
      Boolean(form.preferred_language),
      Boolean(form.career_goal_timeline),
    ];

    const done = checks.filter(Boolean).length;

    return Math.round((done / checks.length) * 100);
  }, [form]);

  const filteredSkills = useMemo(() => {
    const query = skillSearch.trim().toLowerCase();

    if (!query) return skillOptions;

    return skillOptions.filter((skill) => skill.toLowerCase().includes(query));
  }, [skillSearch]);

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoadingProfile(true);

        const profile = await getStudentProfile();
        const parsedPreference = parseStudyPreference(profile?.study_preference);

        setForm({
          ...initialForm,
          age: profile?.age || "",
          academic_level: profile?.academic_level || "",
          class_degree: profile?.class_degree || "",
          marks_cgpa: profile?.marks_cgpa || "",
          favorite_subjects: safeArray(profile?.favorite_subjects),
          weak_subjects: safeArray(profile?.weak_subjects),
          interests: safeArray(profile?.interests),
          skills: safeArray(profile?.skills),
          study_preference: parsedPreference.study_preference,
          weekly_study_hours: parsedPreference.weekly_study_hours,
          preferred_language: parsedPreference.preferred_language,
          career_goal_timeline: parsedPreference.career_goal_timeline,
          education_stream: parsedPreference.education_stream,
          current_institution: parsedPreference.current_institution,
        });

        setHighestStep(6);
      } catch {
        const draft = loadDraft();

        if (draft) {
          setForm({
            ...initialForm,
            ...draft,
            favorite_subjects: safeArray(draft.favorite_subjects),
            weak_subjects: safeArray(draft.weak_subjects),
            interests: safeArray(draft.interests),
            skills: safeArray(draft.skills),
          });
          setDraftLoaded(true);
        }
      } finally {
        setLoadingProfile(false);
      }
    }

    loadProfile();
  }, []);

  useEffect(() => {
    if (loadingProfile) return;

    const timer = setTimeout(() => {
      setAutoSaving(true);
      saveDraft(form);

      setTimeout(() => {
        setAutoSaving(false);
      }, 550);
    }, 800);

    return () => clearTimeout(timer);
  }, [form, loadingProfile]);

  const currentStep = steps.find((item) => item.id === step);

  const updateField = (field, value) => {
    setError("");
    setSuccess("");

    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const toggleArrayField = (field, value) => {
    setError("");
    setSuccess("");

    setForm((prev) => ({
      ...prev,
      [field]: toggleValue(prev[field], value),
    }));
  };

  const addCustomSkill = () => {
    const value = customSkill.trim();

    if (!value) return;

    if (!form.skills.includes(value)) {
      updateField("skills", [...form.skills, value]);
    }

    setCustomSkill("");
  };

  const validateStep = (targetStep = step) => {
    if (targetStep === 1) {
      if (!form.age || !form.academic_level || !form.class_degree || !form.marks_cgpa) {
        return "Please complete age, academic level, class/degree, and marks/CGPA.";
      }

      if (Number(form.age) < 10 || Number(form.age) > 80) {
        return "Please enter a valid age.";
      }

      if (Number(form.marks_cgpa) <= 0) {
        return "Please enter valid marks or CGPA.";
      }
    }

    if (targetStep === 2 && form.favorite_subjects.length === 0) {
      return "Please select at least one favorite subject.";
    }

    if (targetStep === 3 && form.interests.length === 0) {
      return "Please select at least one interest.";
    }

    if (targetStep === 4 && form.skills.length === 0) {
      return "Please select at least one skill.";
    }

    if (targetStep === 5) {
      if (!form.study_preference) {
        return "Please select your learning preference.";
      }

      if (!form.weekly_study_hours) {
        return "Please enter weekly available study hours.";
      }

      if (!form.preferred_language) {
        return "Please select preferred learning language.";
      }

      if (!form.career_goal_timeline) {
        return "Please select your career goal timeline.";
      }
    }

    return "";
  };

  const validateAllSteps = () => {
    for (let index = 1; index <= 5; index += 1) {
      const validationMessage = validateStep(index);

      if (validationMessage) {
        setStep(index);
        setError(validationMessage);
        return false;
      }
    }

    return true;
  };

  const goNext = () => {
    const validationMessage = validateStep();

    if (validationMessage) {
      setError(validationMessage);
      return;
    }

    saveDraft(form);
    setError("");
    setSuccess("Step saved successfully.");

    const nextStep = Math.min(step + 1, 6);
    setStep(nextStep);
    setHighestStep((prev) => Math.max(prev, nextStep));
  };

  const goBack = () => {
    setError("");
    setSuccess("");
    setStep((prev) => Math.max(prev - 1, 1));
  };

  const handleStepClick = (targetStep) => {
    if (targetStep <= highestStep) {
      setError("");
      setSuccess("");
      setStep(targetStep);
      return;
    }

    const validationMessage = validateStep(step);

    if (validationMessage) {
      setError(validationMessage);
      return;
    }

    setHighestStep(targetStep);
    setStep(targetStep);
  };

  const buildBackendPayload = () => {
    const preferenceParts = [
      form.study_preference,
      form.weekly_study_hours
        ? `Weekly study hours: ${form.weekly_study_hours}`
        : "",
      form.preferred_language
        ? `Preferred language: ${form.preferred_language}`
        : "",
      form.career_goal_timeline
        ? `Career goal timeline: ${form.career_goal_timeline}`
        : "",
      form.education_stream ? `Education stream: ${form.education_stream}` : "",
      form.current_institution
        ? `Current institution: ${form.current_institution}`
        : "",
    ].filter(Boolean);

    return {
      age: String(form.age || ""),
      academic_level: form.academic_level,
      class_degree: form.class_degree,
      marks_cgpa: Number(form.marks_cgpa) || 0,
      favorite_subjects: form.favorite_subjects,
      weak_subjects: form.weak_subjects,
      interests: form.interests,
      skills: form.skills,
      study_preference: preferenceParts.join(" | "),
    };
  };

  const handleSaveProfile = async () => {
    setError("");
    setSuccess("");

    if (!validateAllSteps()) {
      return false;
    }

    try {
      setSaving(true);

      const payload = buildBackendPayload();

      await saveStudentProfile(payload);

      localStorage.removeItem(DRAFT_KEY);
      setSuccess("Profile saved successfully.");

      return true;
    } catch (error) {
      console.error(error);
      setError(error.message || "Profile could not be saved.");
      return false;
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateRecommendations = async () => {
    const saved = await handleSaveProfile();

    if (!saved) return;

    try {
      setGenerating(true);
      setSuccess("Generating your AI career recommendations...");

      await generateRecommendations();

      navigate("/recommendations", { replace: true });
    } catch (error) {
      console.error(error);
      setError(
        error.message ||
          "Profile saved, but recommendations could not be generated."
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleSkip = () => {
    saveDraft(form);
    navigate("/dashboard");
  };

  const handleClearDraft = () => {
    localStorage.removeItem(DRAFT_KEY);
    setForm(initialForm);
    setStep(1);
    setHighestStep(1);
    setDraftLoaded(false);
    setSuccess("Draft cleared successfully.");
    setError("");
  };

  if (loadingProfile) {
    return (
      <div className="profile-setup-loading">
        <div className="profile-loader"></div>
        <p>Preparing your AI profile setup...</p>
      </div>
    );
  }

  return (
    <div className="profile-setup-page">
      <aside className="profile-setup-sidebar">
        <Link to="/" className="profile-setup-brand">
          <span>
            <FaCompass />
          </span>
          <div>
            <strong>Career Compass AI</strong>
            <small>Profile Setup</small>
          </div>
        </Link>

        <nav className="setup-steps">
          {steps.map((item) => {
            const isActive = item.id === step;
            const isDone = item.id < step || highestStep > item.id;
            const isLocked = item.id > highestStep;

            return (
              <button
                type="button"
                key={item.id}
                className={[
                  "setup-step",
                  isActive ? "active" : "",
                  isDone && !isActive ? "done" : "",
                  isLocked ? "locked" : "",
                ].join(" ")}
                onClick={() => handleStepClick(item.id)}
              >
                <span>{isDone && !isActive ? <FaCheck /> : item.icon}</span>
                <strong>{item.title}</strong>
              </button>
            );
          })}
        </nav>

        <div className="setup-ai-prompt">
          <div>
            <FaRobot />
            <strong>AI Prompt</strong>
          </div>
          <p>
            Complete your profile to unlock accurate recommendations tailored to
            your unique academic DNA.
          </p>
        </div>
      </aside>

      <main className="profile-setup-main">
        <header className="profile-setup-header">
          <div>
            <span className="profile-ai-badge">
              <FaRobot />
              AI Personalization Engine
            </span>
            <h1>Build Your Career Profile</h1>
            <p>
              Tell us about your academics, interests, and skills so our AI can
              recommend the best career paths for you.
            </p>
          </div>

          <div className="completion-box">
            <strong>{completion}% Completed</strong>
            <div>
              <span style={{ width: `${completion}%` }}></span>
            </div>
          </div>
        </header>

        {draftLoaded && (
          <motion.div
            className="setup-alert success"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
          >
            Draft restored from your previous session.
          </motion.div>
        )}

        {(error || success) && (
          <motion.div
            className={error ? "setup-alert error" : "setup-alert success"}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {error || success}
          </motion.div>
        )}

        <motion.section
          className="profile-form-card"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="profile-form-top">
            <div className="step-title">
              <span>{currentStep.icon}</span>
              <div>
                <h2>{currentStep.title}</h2>
                <p>Step {step} of 6</p>
              </div>
            </div>

            <div className="autosave-pill">
              <FaSave />
              {autoSaving ? "Auto-saving..." : "Draft saved"}
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -24 }}
              transition={{ duration: 0.25 }}
              className="setup-step-content"
            >
              {step === 1 && (
                <div className="setup-grid">
                  <div className="setup-field">
                    <label>Age</label>
                    <input
                      type="number"
                      placeholder="e.g. 20"
                      value={form.age}
                      onChange={(e) => updateField("age", e.target.value)}
                    />
                  </div>

                  <div className="setup-field">
                    <label>Academic Level</label>
                    <select
                      value={form.academic_level}
                      onChange={(e) =>
                        updateField("academic_level", e.target.value)
                      }
                    >
                      <option value="">Select your level</option>
                      <option value="Matric">Matric</option>
                      <option value="Intermediate">Intermediate</option>
                      <option value="Bachelor">Bachelor</option>
                      <option value="Master">Master</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div className="setup-field">
                    <label>Class / Current Degree</label>
                    <input
                      type="text"
                      placeholder="e.g. BS Computer Science"
                      value={form.class_degree}
                      onChange={(e) =>
                        updateField("class_degree", e.target.value)
                      }
                    />
                  </div>

                  <div className="setup-field">
                    <label>Marks or CGPA</label>
                    <input
                      type="number"
                      placeholder="e.g. 82 or 3.5"
                      value={form.marks_cgpa}
                      onChange={(e) =>
                        updateField("marks_cgpa", e.target.value)
                      }
                    />
                  </div>

                  <div className="setup-field">
                    <label>Education Stream</label>
                    <select
                      value={form.education_stream}
                      onChange={(e) =>
                        updateField("education_stream", e.target.value)
                      }
                    >
                      <option value="">Select stream</option>
                      <option value="Science & Technology">
                        Science & Technology
                      </option>
                      <option value="Pre Medical">Pre Medical</option>
                      <option value="Pre Engineering">Pre Engineering</option>
                      <option value="Commerce & Management">
                        Commerce & Management
                      </option>
                      <option value="Humanities & Arts">Humanities & Arts</option>
                    </select>
                  </div>

                  <div className="setup-field">
                    <label>Current Institution</label>
                    <input
                      type="text"
                      placeholder="e.g. University / College name"
                      value={form.current_institution}
                      onChange={(e) =>
                        updateField("current_institution", e.target.value)
                      }
                    />
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="subject-section">
                  <div>
                    <h3>Favorite Subjects</h3>
                    <p>Select subjects you enjoy and perform well in.</p>

                    <div className="chip-grid">
                      {subjects.map((subject) => (
                        <button
                          type="button"
                          key={`fav-${subject}`}
                          className={
                            form.favorite_subjects.includes(subject)
                              ? "chip selected"
                              : "chip"
                          }
                          onClick={() =>
                            toggleArrayField("favorite_subjects", subject)
                          }
                        >
                          {subject}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3>Weak Subjects</h3>
                    <p>Select subjects where you need improvement.</p>

                    <div className="chip-grid">
                      {subjects.map((subject) => (
                        <button
                          type="button"
                          key={`weak-${subject}`}
                          className={
                            form.weak_subjects.includes(subject)
                              ? "chip weak selected"
                              : "chip weak"
                          }
                          onClick={() =>
                            toggleArrayField("weak_subjects", subject)
                          }
                        >
                          {subject}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div>
                  <h3 className="setup-section-title">
                    What are you interested in?
                  </h3>

                  <div className="interest-grid">
                    {interestOptions.map((interest) => (
                      <motion.button
                        type="button"
                        key={interest}
                        className={
                          form.interests.includes(interest)
                            ? "interest-card selected"
                            : "interest-card"
                        }
                        whileHover={{ y: -5 }}
                        onClick={() => toggleArrayField("interests", interest)}
                      >
                        <FaBrain />
                        <span>{interest}</span>
                      </motion.button>
                    ))}
                  </div>
                </div>
              )}

              {step === 4 && (
                <div>
                  <div className="skill-search">
                    <FaSearch />
                    <input
                      type="text"
                      placeholder="Search skills..."
                      value={skillSearch}
                      onChange={(e) => setSkillSearch(e.target.value)}
                    />
                  </div>

                  <div className="chip-grid">
                    {filteredSkills.map((skill) => (
                      <button
                        type="button"
                        key={skill}
                        className={
                          form.skills.includes(skill) ? "chip selected" : "chip"
                        }
                        onClick={() => toggleArrayField("skills", skill)}
                      >
                        {skill}
                      </button>
                    ))}
                  </div>

                  <div className="custom-skill-row">
                    <input
                      type="text"
                      placeholder="Add custom skill"
                      value={customSkill}
                      onChange={(e) => setCustomSkill(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addCustomSkill();
                        }
                      }}
                    />
                    <button type="button" onClick={addCustomSkill}>
                      <FaPlus />
                      Add
                    </button>
                  </div>
                </div>
              )}

              {step === 5 && (
                <div>
                  <h3 className="setup-section-title">
                    How do you prefer to learn?
                  </h3>

                  <div className="learning-grid">
                    {learningOptions.map((option) => (
                      <motion.button
                        type="button"
                        key={option}
                        className={
                          form.study_preference === option
                            ? "learning-card selected"
                            : "learning-card"
                        }
                        whileHover={{ y: -5 }}
                        onClick={() => updateField("study_preference", option)}
                      >
                        <FaLightbulb />
                        <span>{option}</span>
                      </motion.button>
                    ))}
                  </div>

                  <div className="setup-grid extra-preferences">
                    <div className="setup-field">
                      <label>Weekly Available Study Hours</label>
                      <input
                        type="number"
                        placeholder="e.g. 10"
                        value={form.weekly_study_hours}
                        onChange={(e) =>
                          updateField("weekly_study_hours", e.target.value)
                        }
                      />
                    </div>

                    <div className="setup-field">
                      <label>Preferred Learning Language</label>
                      <select
                        value={form.preferred_language}
                        onChange={(e) =>
                          updateField("preferred_language", e.target.value)
                        }
                      >
                        <option value="">Select language</option>
                        <option value="English">English</option>
                        <option value="Urdu">Urdu</option>
                        <option value="English + Urdu">English + Urdu</option>
                      </select>
                    </div>

                    <div className="setup-field">
                      <label>Career Goal Timeline</label>
                      <select
                        value={form.career_goal_timeline}
                        onChange={(e) =>
                          updateField("career_goal_timeline", e.target.value)
                        }
                      >
                        <option value="">Select timeline</option>
                        <option value="3 months">3 months</option>
                        <option value="6 months">6 months</option>
                        <option value="1 year">1 year</option>
                        <option value="2 years">2 years</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {step === 6 && (
                <div className="review-grid">
                  <div className="review-card">
                    <h3>Academic Profile</h3>
                    <p>{form.academic_level || "Not selected"}</p>
                    <p>{form.class_degree || "Degree not added"}</p>
                    <p>Marks/CGPA: {form.marks_cgpa || "N/A"}</p>
                    <p>Stream: {form.education_stream || "N/A"}</p>
                    <p>Institution: {form.current_institution || "N/A"}</p>
                  </div>

                  <div className="review-card">
                    <h3>Strong Subjects</h3>
                    <div className="tag-list">
                      {form.favorite_subjects.map((item) => (
                        <span key={item}>{item}</span>
                      ))}
                    </div>
                  </div>

                  <div className="review-card">
                    <h3>Weak Subjects</h3>
                    <div className="tag-list weak">
                      {form.weak_subjects.map((item) => (
                        <span key={item}>{item}</span>
                      ))}
                    </div>
                  </div>

                  <div className="review-card">
                    <h3>Interests</h3>
                    <div className="tag-list">
                      {form.interests.map((item) => (
                        <span key={item}>{item}</span>
                      ))}
                    </div>
                  </div>

                  <div className="review-card">
                    <h3>Skills</h3>
                    <div className="tag-list">
                      {form.skills.map((item) => (
                        <span key={item}>{item}</span>
                      ))}
                    </div>
                  </div>

                  <div className="readiness-card">
                    <h3>Profile Readiness</h3>
                    <strong>{completion}%</strong>
                    <p>
                      More complete profile data helps Career Compass AI generate
                      better recommendations.
                    </p>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          <div className="setup-actions">
            <button
              type="button"
              className="back-btn"
              onClick={step === 1 ? () => navigate("/welcome") : goBack}
            >
              <FaArrowLeft />
              {step === 1 ? "Back to Welcome" : "Back"}
            </button>

            <div>
              <button type="button" className="skip-btn" onClick={handleSkip}>
                Skip for now
              </button>

              {draftLoaded && (
                <button
                  type="button"
                  className="skip-btn"
                  onClick={handleClearDraft}
                >
                  Clear Draft
                </button>
              )}

              {step < 6 ? (
                <button type="button" className="primary-action" onClick={goNext}>
                  Save & Continue
                  <FaArrowRight />
                </button>
              ) : (
                <button
                  type="button"
                  className="primary-action"
                  onClick={handleGenerateRecommendations}
                  disabled={saving || generating}
                >
                  {generating
                    ? "Generating..."
                    : saving
                    ? "Saving..."
                    : "Generate Career Recommendations"}
                  <FaArrowRight />
                </button>
              )}
            </div>
          </div>
        </motion.section>

        <div className="profile-support-grid">
          <div className="students-card">
            <img
              src="https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=900&q=80"
              alt="students"
            />
            <div>Join 50,000+ students navigating their futures</div>
          </div>

          <div className="did-you-know">
            <FaBrain />
            <h3>Did you know?</h3>
            <p>
              Profiles with complete academic info receive more accurate career
              matching.
            </p>
          </div>
        </div>
      </main>

      <Link to="/chatbot" className="profile-floating-ai">
        <FaRobot />
        <span></span>
      </Link>
    </div>
  );
}

export default ProfileSetup;