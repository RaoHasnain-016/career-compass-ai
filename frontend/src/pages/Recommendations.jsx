import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  FaBolt,
  FaBookOpen,
  FaBookmark,
  FaBrain,
  FaChartBar,
  FaChartPie,
  FaCheckCircle,
  FaCompass,
  FaDownload,
  FaExclamationCircle,
  FaFilter,
  FaHome,
  FaMagic,
  FaRegBookmark,
  FaRobot,
  FaRoute,
  FaSearch,
  FaSignOutAlt,
  FaStar,
  FaSyncAlt,
  FaUser,
} from "react-icons/fa";
import { signOut } from "firebase/auth";
import { auth } from "../firebase/firebase";
import Sidebar from "../components/Sidebar";
import NotificationBell from "../components/NotificationBell";
import {
  generateCareerRecommendations,
  getMyRecommendationRanking,
  getSavedCareers,
  saveCareer,
  updateRecommendationFeedback,
} from "../services/recommendationService";
import { removeSavedCareer } from "../services/savedCareerService";
import { getStudentProfile, selectCareer } from "../services/profileService";
import { downloadCareerReport } from "../services/reportService";
import "../styles/recommendations-page.css";
import "../styles/student-layout.css";

const filterOptions = [
  "All",
  "Technology",
  "Medical",
  "Business",
  "Design",
  "Education",
  "Data",
  "High Match",
];

const rankingModes = { model: "model", personalized: "personalized" };
const personalizationLabels = {
  saved_career: "Based on your saved career",
  saved_field: "Related to a career you saved",
  feedback_helpful: "You marked this career as helpful",
  feedback_less_relevant: "You marked this career as less relevant",
  feedback_field_helpful: "Related to a career you found helpful",
  feedback_field_less_relevant: "Related to a career you found less relevant",
};

const navLinks = [
  { label: "Dashboard", path: "/dashboard", icon: <FaHome /> },
  { label: "Profile", path: "/profile", icon: <FaUser /> },
  { label: "Recommendations", path: "/recommendations", icon: <FaMagic /> },
  { label: "Roadmap", path: "/roadmap", icon: <FaRoute /> },
  { label: "Skill Gap Analysis", path: "/skill-gap", icon: <FaChartBar /> },
  { label: "Learning Resources", path: "/resources", icon: <FaBookOpen /> },
  { label: "Saved Careers", path: "/saved-careers", icon: <FaBookmark /> },
  { label: "Chatbot", path: "/chatbot", icon: <FaRobot /> },
];

function asArray(value) {
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

function getScore(item) {
  return Math.round(Number(item.match_score || item.score || 0));
}

function getCareerTitle(item) {
  return item.title || item.career_title || item?.career?.title || "Career Path";
}

function getCareerField(item) {
  return item.field || item.career_field || item?.career?.field || "General";
}

function getBadge(index, score) {
  if (index === 0 || score >= 90) return "Best Match";
  if (score >= 80) return "Strong Match";
  return "Good Option";
}

function getBadgeClass(score) {
  if (score >= 90) return "best";
  if (score >= 80) return "strong";
  return "good";
}

function getIconForCareer(title) {
  const lower = title.toLowerCase();

  if (lower.includes("data")) return <FaChartBar />;
  if (lower.includes("ai") || lower.includes("machine")) return <FaBrain />;
  if (lower.includes("software") || lower.includes("developer")) return <FaCompass />;
  if (lower.includes("doctor") || lower.includes("medical")) return <FaCheckCircle />;
  if (lower.includes("design")) return <FaMagic />;

  return <FaStar />;
}

function getUserName() {
  return (
    auth.currentUser?.displayName ||
    auth.currentUser?.email?.split("@")[0] ||
    "Student"
  );
}

function Recommendations() {
  const navigate = useNavigate();

  const [recommendations, setRecommendations] = useState([]);
  const [savedCareerIds, setSavedCareerIds] = useState([]);
  const [activeFilter, setActiveFilter] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("recommended");
  const [modelRankingAvailable, setModelRankingAvailable] = useState(false);
  const [changingRanking, setChangingRanking] = useState(false);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [savingId, setSavingId] = useState("");
  const [selectedCareerId, setSelectedCareerId] = useState("");
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  async function loadRecommendations() {
    try {
      setLoading(true);
      setError("");

      const [recommendationData, savedData, profileData] = await Promise.all([
        getMyRecommendationRanking(sortBy === "personalized" ? "personalized" : "rules"),
        getSavedCareers(),
        getStudentProfile().catch(() => null),
      ]);

      setRecommendations(recommendationData.recommendations);
      setModelRankingAvailable(recommendationData.modelRankingAvailable);
      setSortBy((current) => current === "model" ? "recommended" : current);

      const ids = savedData
        .map((item) => item.career_id || item.career?.career_id)
        .filter(Boolean);

      setSavedCareerIds(ids);
      setProfile(profileData);
      setSelectedCareerId(profileData?.selected_career_id || "");
    } catch (error) {
      console.error(error);
      setError(
        error.message ||
          "Recommendations could not be loaded. Please complete your profile first."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRecommendations();
  }, []);

  async function handleSortChange(event) {
    const nextSort = event.target.value;
    const ranking = rankingModes[nextSort] || "rules";

    if (ranking === (rankingModes[sortBy] || "rules")) {
      setSortBy(nextSort);
      return;
    }

    setChangingRanking(true);
    setError("");
    try {
      const result = await getMyRecommendationRanking(ranking);
      setModelRankingAvailable(result.modelRankingAvailable);

      if (ranking === "model" && result.rankingSource !== "trained") {
        setError("The trained ranking is unavailable for these recommendations. The standard ranking is still available.");
        return;
      }

      setRecommendations(result.recommendations);
      setSortBy(nextSort);
    } catch (error) {
      setError(error.message || "The ranking could not be changed. Please try again.");
    } finally {
      setChangingRanking(false);
    }
  }

  const filteredRecommendations = useMemo(() => {
    let result = [...recommendations];

    const query = searchQuery.trim().toLowerCase();

    if (query) {
      result = result.filter((item) => {
        const title = getCareerTitle(item).toLowerCase();
        const field = getCareerField(item).toLowerCase();
        const skills = [
          ...asArray(item.matched_skills),
          ...asArray(item.missing_skills),
          ...asArray(item.required_skills),
        ]
          .join(" ")
          .toLowerCase();

        return title.includes(query) || field.includes(query) || skills.includes(query);
      });
    }

    if (activeFilter !== "All") {
      if (activeFilter === "High Match") {
        result = result.filter((item) => getScore(item) >= 80);
      } else {
        result = result.filter((item) =>
          getCareerField(item).toLowerCase().includes(activeFilter.toLowerCase())
        );
      }
    }

    if (sortBy === "match_score") {
      result.sort((a, b) => getScore(b) - getScore(a));
    }

    if (sortBy === "field") {
      result.sort((a, b) => getCareerField(a).localeCompare(getCareerField(b)));
    }

    if (sortBy === "difficulty") {
      result.sort((a, b) =>
        String(a.difficulty_level || "").localeCompare(String(b.difficulty_level || ""))
      );
    }

    return result;
  }, [recommendations, activeFilter, searchQuery, sortBy]);

  const analytics = useMemo(() => {
    const total = recommendations.length;
    const highestScore = recommendations.length
      ? Math.max(...recommendations.map((item) => getScore(item)))
      : 0;

    const topCareer = recommendations.length ? recommendations[0] : null;

    const fieldCounts = recommendations.reduce((acc, item) => {
      const field = getCareerField(item);
      acc[field] = (acc[field] || 0) + 1;
      return acc;
    }, {});

    const fieldData = Object.entries(fieldCounts).map(([name, value], index) => ({
      name,
      value,
      color: ["#0b67c2", "#7c3aed", "#06b6d4", "#10b981", "#f97316"][index % 5],
    }));

    const chartData = recommendations.slice(0, 5).map((item) => ({
      name: getCareerTitle(item),
      score: getScore(item),
    }));

    const matchedSkills = asArray(topCareer?.matched_skills).length;
    const missingSkills = asArray(topCareer?.missing_skills).length;
    const totalSkills = Math.max(matchedSkills + missingSkills, 1);

    return {
      total,
      highestScore,
      strongestField: topCareer ? getCareerField(topCareer) : "Not available",
      topCareer,
      chartData,
      fieldData,
      readiness: highestScore,
      skillReadyPercent: Math.round((matchedSkills / totalSkills) * 100),
      missingSkills,
    };
  }, [recommendations]);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setError("");

      await generateCareerRecommendations();
      await loadRecommendations();
    } catch (error) {
      console.error(error);
      setError(
        error.message ||
          "Could not regenerate recommendations. Please complete your profile first."
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleBookmark = async (careerId, isSaved) => {
    if (!careerId) return;

    setSavingId(careerId);
    setError("");
    try {
      if (isSaved) {
        await removeSavedCareer(careerId);
        setSavedCareerIds((ids) => ids.filter((id) => id !== careerId));
      } else {
        await saveCareer(careerId);
        setSavedCareerIds((ids) => [...ids, careerId]);
      }
      if (sortBy === "personalized") {
        try {
          const result = await getMyRecommendationRanking("personalized");
          setRecommendations(result.recommendations);
        } catch {
          setError("Bookmark updated. Reload this page to refresh your personalized ranking.");
        }
      }
    } catch (error) {
      console.error(error);
      setError(error.message || "The bookmark could not be updated.");
    } finally {
      setSavingId("");
    }
  };

  const handleChooseCareer = async (careerId) => {
    try {
      setSavingId(careerId);
      await selectCareer(careerId);
      setSelectedCareerId(careerId);
    } catch (error) {
      setError(error.message || "Career selection could not be saved.");
    } finally {
      setSavingId("");
    }
  };

  async function handleFeedback(careerId, feedback) {
    if (!careerId || savingId || changingRanking || generating) return;

    setSavingId(careerId);
    setError("");
    try {
      const result = await updateRecommendationFeedback(careerId, feedback);
      setRecommendations((items) => items.map((item) =>
        (item.career_id || item.career?.career_id) === careerId
          ? { ...item, feedback: result.feedback }
          : item
      ));
      if (sortBy === "personalized") {
        try {
          const ranking = await getMyRecommendationRanking("personalized");
          setRecommendations(ranking.recommendations);
        } catch {
          setError("Feedback saved. Reload to refresh your personalized order.");
        }
      }
    } catch (error) {
      setError(error.message || "Could not save your feedback.");
    } finally {
      setSavingId("");
    }
  }

  const handleDownloadReport = () => {
    downloadCareerReport({
      profile,
      recommendations,
      selectedCareerId,
      name: getUserName(),
    });
  };

  const handleLogout = async () => {
    await signOut(auth);
    navigate("/login", { replace: true });
  };

  if (loading) {
    return (
      <div className="recommendations-loading">
        <div className="ai-loader">
          <FaRobot />
        </div>
        <h2>Analyzing your profile...</h2>
        <p>Comparing your skills, interests, subjects, and career paths.</p>
      </div>
    );
  }

  return (
    <div className="recommendations-page student-shell">
      <Sidebar />
      <main className="rec-main student-main">
        <header className="rec-topbar">
          <div className="rec-top-left">
            <strong>Career Compass AI</strong>
            <span>Welcome back, {getUserName()}</span>
          </div>

          <div className="rec-top-actions">
            <div className="rec-search">
              <FaSearch />
              <input
                type="text"
                placeholder="Search insights..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <NotificationBell />

            <img
              src={
                auth.currentUser?.photoURL ||
                "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=120&q=80"
              }
              alt="profile"
            />
          </div>
        </header>

        <section className="rec-content">
          <div className="rec-page-heading">
            <div>
              <h1>Career Recommendations</h1>
              <p>
                Career paths based on your academic profile,
                interests, skills, and performance.
              </p>
            </div>

            <div className="rec-heading-actions">
              <select
                aria-label="Sort recommendations"
                aria-busy={changingRanking}
                value={sortBy}
                onChange={handleSortChange}
                disabled={changingRanking || generating || !!savingId}
              >
                <option value="recommended">Recommended Order</option>
                <option value="personalized">Personalized Order</option>
                {modelRankingAvailable && recommendations.length > 1 && (
                  <option value="model">Preview Trained Ranking</option>
                )}
                <option value="match_score">Sort by Match Score</option>
                <option value="field">Sort by Field</option>
                <option value="difficulty">Sort by Difficulty</option>
              </select>

              <button type="button" className="filter-btn">
                <FaFilter />
                Filter
              </button>

              <button
                type="button"
                className="regenerate-btn"
                onClick={handleGenerate}
                disabled={generating || changingRanking || !!savingId}
              >
                <FaSyncAlt className={generating ? "spin-icon" : ""} />
                {generating ? "Generating..." : "Generate More Careers"}
              </button>
              <button type="button" className="report-btn" onClick={handleDownloadReport} disabled={!recommendations.length || changingRanking}>
                <FaDownload /> Download Report
              </button>
            </div>
          </div>

          {error && <div className="rec-error" role="alert">{error}</div>}

          {recommendations.length > 0 && (
            <p className="rec-ranking-hint">
              Rate your matches to improve Personalized Order. Select a rating again to clear it.
            </p>
          )}

          {recommendations.length === 0 ? (
            <div className="rec-empty-state">
              <FaRobot />
              <h2>No recommendations yet</h2>
              <p>
                Complete your profile and generate recommendations to see your
                personalized AI career paths.
              </p>
              <div>
                <Link to="/profile-setup">Complete Profile</Link>
                <button type="button" onClick={handleGenerate} disabled={generating}>
                  {generating ? "Generating..." : "Generate Recommendations"}
                </button>
              </div>
            </div>
          ) : (
            <div className="rec-grid">
              <div className="rec-feed">
                <motion.div
                  className="rec-hero-card"
                  initial={{ opacity: 0, y: 24 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="rec-hero-info">
                    <span>
                      <FaMagic />
                      {sortBy === "model" ? "Trained Ranking Preview" : sortBy === "personalized" ? "Feedback and Saved Careers" : "Profile-Based Matches"}
                    </span>

                    <h2>Your Best Career Matches</h2>

                    <div className="rec-hero-stats">
                      <div>
                        <small>Analyzed</small>
                        <strong>{analytics.total || 0}</strong>
                      </div>
                      <div>
                        <small>Highest Match</small>
                        <strong>{analytics.highestScore}%</strong>
                      </div>
                      <div>
                        <small>First Suggested Field</small>
                        <strong>{analytics.strongestField}</strong>
                      </div>
                    </div>
                  </div>

                  <div className="rec-readiness-ring">
                    <ResponsiveContainer width="100%" height={180}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: "Ready", value: analytics.readiness },
                            {
                              name: "Remaining",
                              value: 100 - analytics.readiness,
                            },
                          ]}
                          innerRadius={62}
                          outerRadius={82}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          <Cell fill="#ffffff" />
                          <Cell fill="rgba(255,255,255,0.2)" />
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>

                    <div>
                      <strong>{analytics.readiness}%</strong>
                      <span>Readiness</span>
                    </div>
                  </div>
                </motion.div>

                <div className="rec-filter-chips">
                  {filterOptions.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={activeFilter === option ? "active" : ""}
                      onClick={() => setActiveFilter(option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>

                <div className="rec-card-list">
                  {filteredRecommendations.length === 0 && (
                    <div className="rec-inline-empty">
                      No careers match the current search and filter settings.
                    </div>
                  )}

                  {filteredRecommendations.map((item, index) => {
                    const score = getScore(item);
                    const title = getCareerTitle(item);
                    const careerId = item.career_id || item?.career?.career_id;
                    const isSaved = savedCareerIds.includes(careerId);
                    const isSelected = selectedCareerId === careerId;
                    const matchedSkills = asArray(item.matched_skills);
                    const missingSkills = asArray(item.missing_skills);
                    const matchedSubjects = asArray(item.matched_subjects);
                    const missingSubjects = asArray(item.missing_subjects);

                    return (
                      <motion.article
                        key={item.recommendation_id || careerId || title}
                        className={`rec-career-card ${getBadgeClass(score)}`}
                        initial={{ opacity: 0, y: 24 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.08 }}
                        whileHover={{ y: -8 }}
                      >
                        <div className="rec-card-header">
                          <div className="rec-title-area">
                            <div className="rec-career-icon">
                              {getIconForCareer(title)}
                            </div>

                            <div>
                              <div className="rec-title-row">
                                <h2>{title}</h2>
                                <span className={`match-badge ${getBadgeClass(score)}`}>
                                  {item.model_rank ? `Rank #${item.model_rank}` : getBadge(sortBy === "personalized" ? -1 : index, score)}
                                </span>
                              </div>

                              <p>
                                {item.overview ||
                                  item.explanation ||
                                  `${getCareerField(item)} career path matched with your profile.`}
                              </p>
                            </div>
                          </div>

                          <div className="rec-score">
                            <strong>{score}%</strong>
                            <span>{item.model_rank || sortBy === "personalized" ? "Rule Match Score" : "Match Score"}</span>
                          </div>
                        </div>

                        <div className="rec-meta-row">
                          <span>{getCareerField(item)}</span>
                          <span>{item.confidence_level || "High Confidence"}</span>
                          <span>{item.eligibility_status || "Eligible"}</span>
                          <span>{item.difficulty_level || "Medium Difficulty"}</span>
                          {item.personalization_reason && <span>{personalizationLabels[item.personalization_reason]}</span>}
                        </div>

                        <div className="rec-skills-grid">
                          <div>
                            <h4>
                              <FaCheckCircle />
                              Matched Skills
                            </h4>
                            <div className="rec-chip-list matched">
                              {(matchedSkills.length ? matchedSkills : ["Profile Match"])
                                .slice(0, 5)
                                .map((skill) => (
                                  <span key={skill}>{skill}</span>
                                ))}
                            </div>
                          </div>

                          <div>
                            <h4>
                              <FaExclamationCircle />
                              Missing Skills
                            </h4>
                            <div className="rec-chip-list missing">
                              {(missingSkills.length ? missingSkills : ["No major gap"])
                                .slice(0, 5)
                                .map((skill) => (
                                  <span key={skill}>{skill}</span>
                                ))}
                            </div>
                          </div>
                        </div>

                        {(matchedSubjects.length > 0 || missingSubjects.length > 0) && (
                          <div className="rec-subject-row">
                            {matchedSubjects.slice(0, 3).map((subject) => (
                              <span key={subject}>{subject}</span>
                            ))}
                            {missingSubjects.slice(0, 3).map((subject) => (
                              <span key={subject} className="missing">
                                {subject}
                              </span>
                            ))}
                          </div>
                        )}

                        {item.improvement_advice && (
                          <p className="rec-advice">
                            <FaBolt />
                            {item.improvement_advice}
                          </p>
                        )}

                        <div className="rec-feedback" role="group" aria-label={`Feedback for ${title}`}>
                          <button
                            type="button"
                            aria-pressed={item.feedback === "helpful"}
                            disabled={!careerId || !!savingId || changingRanking || generating}
                            onClick={() => handleFeedback(careerId, item.feedback === "helpful" ? null : "helpful")}
                          >
                            Helpful
                          </button>
                          <button
                            type="button"
                            aria-pressed={item.feedback === "less_relevant"}
                            disabled={!careerId || !!savingId || changingRanking || generating}
                            onClick={() => handleFeedback(careerId, item.feedback === "less_relevant" ? null : "less_relevant")}
                          >
                            Less relevant
                          </button>
                        </div>

                        <div className="rec-card-actions">
                          <div>
                            <Link to={`/career/${careerId}`} state={{ recommendation: item }}>
                              View Details
                            </Link>
                            <Link
                              to={`/roadmap?careerId=${careerId}`}
                              state={{ careerId, careerTitle: title }}
                            >
                              View Roadmap
                            </Link>
                            <button
                              type="button"
                              className={isSelected ? "selected-career-btn" : "choose-career-btn"}
                              onClick={() => handleChooseCareer(careerId)}
                              disabled={!!savingId || changingRanking || generating || isSelected}
                            >
                              {isSelected ? "Selected Career" : "Choose Career"}
                            </button>
                          </div>

                          <div>
                            <button
                              type="button"
                              className={isSaved ? "saved" : ""}
                              onClick={() => handleBookmark(careerId, isSaved)}
                              disabled={!!savingId || changingRanking || generating}
                              aria-label={isSaved ? `Remove ${title} from saved careers` : `Save ${title}`}
                              title={isSaved ? "Remove Saved Career" : "Save Career"}
                            >
                              {isSaved ? <FaBookmark /> : <FaRegBookmark />}
                            </button>

                            <Link
                              to="/chatbot"
                              className="ask-ai-btn"
                              state={{ careerId, careerTitle: title }}
                            >
                              <FaRobot />
                              Ask AI
                            </Link>
                          </div>
                        </div>
                      </motion.article>
                    );
                  })}
                </div>
              </div>

              <aside className="rec-analytics">
                <motion.div
                  className="rec-analytics-card"
                  initial={{ opacity: 0, x: 24 }}
                  animate={{ opacity: 1, x: 0 }}
                >
                  <h3>
                    <FaChartBar />
                    Match Score Comparison
                  </h3>

                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={analytics.chartData} layout="vertical">
                      <XAxis type="number" domain={[0, 100]} hide />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={110}
                        tick={{ fontSize: 11 }}
                      />
                      <Tooltip />
                      <Bar dataKey="score" fill="#0b67c2" radius={[0, 10, 10, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </motion.div>

                <motion.div
                  className="rec-analytics-card"
                  initial={{ opacity: 0, x: 24 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <h3>
                    <FaChartPie />
                    Career Field Affinity
                  </h3>

                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={analytics.fieldData}
                        innerRadius={58}
                        outerRadius={84}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {analytics.fieldData.map((item) => (
                          <Cell key={item.name} fill={item.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>

                  <div className="field-legend">
                    {analytics.fieldData.map((item) => (
                      <div key={item.name}>
                        <span style={{ background: item.color }}></span>
                        <small>{item.name}</small>
                      </div>
                    ))}
                  </div>
                </motion.div>

                <motion.div
                  className="rec-next-card"
                  initial={{ opacity: 0, x: 24 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <h3>
                    <FaBolt />
                    Next Step Recommendation
                  </h3>

                  <p>
                    For your first recommendation, focus on{" "}
                    <strong>
                      {asArray(analytics.topCareer?.missing_skills)[0] ||
                        "your missing skill gaps"}
                    </strong>{" "}
                    to improve your readiness and career eligibility.
                  </p>

                  <Link to="/resources">Start Bridging Gap</Link>
                </motion.div>
              </aside>
            </div>
          )}
        </section>
      </main>

    </div>
  );
}

export default Recommendations;
