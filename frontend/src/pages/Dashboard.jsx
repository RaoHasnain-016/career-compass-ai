import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  FaBell,
  FaBookmark,
  FaBookOpen,
  FaChartLine,
  FaCheck,
  FaCompass,
  FaGraduationCap,
  FaRobot,
  FaRoute,
  FaSearch,
  FaSignOutAlt,
  FaStar,
  FaUser,
} from "react-icons/fa";
import { signOut } from "firebase/auth";
import { auth } from "../firebase/firebase";
import { getDashboardData } from "../services/dashboardService";
import { generateCareerRecommendations } from "../services/recommendationService";
import "../styles/dashboard-page.css";

const sidebarLinks = [
  { label: "Dashboard", path: "/dashboard", icon: <FaChartLine /> },
  { label: "Profile", path: "/profile", icon: <FaUser /> },
  { label: "Recommendations", path: "/recommendations", icon: <FaStar /> },
  { label: "Roadmap", path: "/roadmap", icon: <FaRoute /> },
  { label: "Skill Gap Analysis", path: "/skill-gap", icon: <FaChartLine /> },
  { label: "Learning Resources", path: "/resources", icon: <FaBookOpen /> },
  { label: "Saved Careers", path: "/saved-careers", icon: <FaBookmark /> },
  { label: "Chatbot", path: "/chatbot", icon: <FaRobot /> },
];

const activityData = [
  { day: "Mon", hours: 1.2 },
  { day: "Tue", hours: 2.4 },
  { day: "Wed", hours: 4.1 },
  { day: "Thu", hours: 0.8 },
  { day: "Fri", hours: 1.8 },
  { day: "Sat", hours: 1.5 },
  { day: "Sun", hours: 0.6 },
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

function getNameFromUser(profile) {
  const firebaseName = auth.currentUser?.displayName;
  const emailName = auth.currentUser?.email?.split("@")[0];

  return (
    profile?.full_name ||
    profile?.name ||
    firebaseName ||
    emailName ||
    "Student"
  );
}

function getCareerTitle(item) {
  return (
    item?.career?.title ||
    item?.title ||
    item?.career_title ||
    "Recommended Career"
  );
}

function getCareerField(item) {
  return item?.career?.field || item?.field || "Career Field";
}

function getMatchScore(item) {
  const raw = item?.match_score || item?.score || item?.percentage || 0;
  return Number(raw) || 0;
}

function getCareerImage(title) {
  const lower = title.toLowerCase();

  if (lower.includes("data")) {
    return "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=500&q=80";
  }

  if (lower.includes("software") || lower.includes("developer")) {
    return "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=500&q=80";
  }

  if (lower.includes("doctor") || lower.includes("medical")) {
    return "https://images.unsplash.com/photo-1584982751601-97dcc096659c?auto=format&fit=crop&w=500&q=80";
  }

  if (lower.includes("design")) {
    return "https://images.unsplash.com/photo-1561070791-2526d30994b5?auto=format&fit=crop&w=500&q=80";
  }

  return "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=500&q=80";
}

function Dashboard() {
  const navigate = useNavigate();

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loadError, setLoadError] = useState("");

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setLoadError("");

      const data = await getDashboardData();
      setDashboardData(data);
    } catch (error) {
      console.error(error);
      setLoadError(
        error.message ||
          "Dashboard data could not be loaded. Please retry after checking the backend connection."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleGenerateRecommendations = async () => {
    try {
      setGenerating(true);
      setLoadError("");
      await generateCareerRecommendations();
      await loadDashboard();
    } catch (error) {
      console.error(error);
      setLoadError(
        error.message ||
          "Recommendations could not be generated. Please complete your profile first."
      );
    } finally {
      setGenerating(false);
    }
  };

  const computed = useMemo(() => {
    const profile = dashboardData?.profile;
    const recommendations = dashboardData?.recommendations || [];
    const topRecommendation = dashboardData?.topRecommendation;
    const career = dashboardData?.career;
    const roadmap = dashboardData?.roadmap || [];
    const resources = dashboardData?.resources || [];
    const videos = dashboardData?.videos || [];

    const userName = getNameFromUser(profile);
    const hasProfile = Boolean(
      profile &&
        (profile.profile_id ||
          profile.academic_level ||
          asArray(profile.skills).length ||
          asArray(profile.interests).length)
    );
    const hasRecommendations = recommendations.length > 0;
    const profileFields = [
      profile?.age,
      profile?.academic_level,
      profile?.class_degree,
      profile?.marks_cgpa,
      profile?.study_preference,
      asArray(profile?.favorite_subjects).length,
      asArray(profile?.weak_subjects).length,
      asArray(profile?.interests).length,
      asArray(profile?.skills).length,
    ];
    const profileCompletion = hasProfile
      ? Math.round(
          (profileFields.filter(Boolean).length / profileFields.length) * 100
        )
      : 0;

    const topScore = getMatchScore(topRecommendation);
    const matchScore = Math.round(topScore || 0);

    const profileSkills = asArray(profile?.skills);
    const requiredSkills = asArray(
      career?.required_skills || topRecommendation?.career?.required_skills
    );

    const matchedSkills = asArray(topRecommendation?.matched_skills);
    const missingSkills = asArray(topRecommendation?.missing_skills);

    const totalSkills = Math.max(
      requiredSkills.length,
      profileSkills.length + missingSkills.length,
      1
    );

    const completedSkills = Math.min(
      matchedSkills.length || profileSkills.length,
      totalSkills
    );

    const missingCount = missingSkills.length;
    const improvingCount = Math.max(totalSkills - completedSkills - missingCount, 0);

    const masteredPercent = Math.round((completedSkills / totalSkills) * 100);
    const improvingPercent = Math.round((improvingCount / totalSkills) * 100);
    const missingPercent = Math.max(100 - masteredPercent - improvingPercent, 0);

    const completedRoadmapStages = roadmap.filter(
      (stage) => stage.completed || stage.is_completed || stage.progress === 100
    ).length;
    const roadmapProgress = roadmap.length
      ? Math.round((completedRoadmapStages / roadmap.length) * 100)
      : 0;

    const learningHours = activityData.reduce((sum, item) => sum + item.hours, 0);

    const careerChartData = recommendations.slice(0, 5).map((item) => ({
      name: getCareerTitle(item),
      score: Math.round(getMatchScore(item)),
    }));

    const skillPieData = [
      { name: "Mastered", value: masteredPercent, color: "#0b67c2" },
      { name: "Improving", value: improvingPercent, color: "#7c3aed" },
      { name: "Missing", value: missingPercent, color: "#ef4444" },
    ];

    const interestStrength = [
      {
        subject: "Programming",
        value:
          profileSkills.some((skill) => skill.toLowerCase().includes("program"))
            ? 95
            : 68,
      },
      {
        subject: "Mathematics",
        value: asArray(profile?.favorite_subjects).some((subject) =>
          subject.toLowerCase().includes("math")
        )
          ? 88
          : 62,
      },
      {
        subject: "Communication",
        value: profileSkills.some((skill) =>
          skill.toLowerCase().includes("communication")
        )
          ? 86
          : 60,
      },
      {
        subject: "Creativity",
        value: asArray(profile?.interests).some((interest) =>
          interest.toLowerCase().includes("design")
        )
          ? 82
          : 56,
      },
      {
        subject: "Problem Solving",
        value: profileSkills.some((skill) =>
          skill.toLowerCase().includes("problem")
        )
          ? 92
          : 70,
      },
    ];

    const roadmapChart = roadmap.length
      ? roadmap.map((stage, index) => ({
          week: `Stage ${index + 1}`,
          progress: Math.round(((index + 1) / roadmap.length) * 100),
        }))
      : [];

    return {
      userName,
      hasProfile,
      hasRecommendations,
      profileCompletion,
      recommendations,
      topRecommendation,
      career,
      roadmap,
      resources,
      videos,
      matchScore,
      roadmapProgress,
      completedSkills,
      totalSkills,
      learningHours,
      missingSkills,
      profileSkills,
      careerChartData,
      skillPieData,
      interestStrength,
      roadmapChart,
      aiCareerTitle: getCareerTitle(topRecommendation),
      aiCareerField: getCareerField(topRecommendation),
    };
  }, [dashboardData]);

  const handleLogout = async () => {
    await signOut(auth);
    navigate("/login", { replace: true });
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="dashboard-loader"></div>
        <p>Building your AI dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <aside className="dashboard-sidebar">
        <Link to="/" className="dashboard-brand">
          <span>
            <FaCompass />
          </span>
          <div>
            <strong>Career Compass AI</strong>
            <small>AI Career Advisor</small>
          </div>
        </Link>

        <nav className="dashboard-nav">
          {sidebarLinks.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={item.path === "/dashboard" ? "active" : ""}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="dashboard-pro-card">
          <p>PRO PLAN</p>
          <span>Unlock advanced AI mentorship and premium roadmap insights.</span>
          <button type="button">Upgrade to Premium</button>
        </div>

        <button type="button" className="logout-btn" onClick={handleLogout}>
          <FaSignOutAlt />
          Logout
        </button>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-topbar">
          <div className="dashboard-search">
            <FaSearch />
            <input placeholder="Search careers, skills, resources..." />
          </div>

          <div className="dashboard-user-area">
            <span>Welcome, {computed.userName}</span>
            <button type="button">
              <FaBell />
            </button>
            <img
              src={
                auth.currentUser?.photoURL ||
                "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=120&q=80"
              }
              alt="profile"
            />
          </div>
        </header>

        <section className="dashboard-content">
          <motion.div
            className="dashboard-hero"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1>Welcome back, {computed.userName} 👋</h1>
            <p>Use your live profile and recommendations to plan the next best career move.</p>
          </motion.div>

          {loadError && (
            <div className="dashboard-warning">
              <span>{loadError}</span>
              <button type="button" onClick={loadDashboard}>
                Retry
              </button>
            </div>
          )}

          {!computed.hasProfile && (
            <div className="dashboard-empty-state">
              <FaUser />
              <div>
                <h2>Complete your student profile</h2>
                <p>
                  Your dashboard unlocks personalized match scores, roadmaps,
                  skill gaps, and learning resources after profile setup.
                </p>
              </div>
              <Link to="/profile-setup">Go to Profile Setup</Link>
            </div>
          )}

          {computed.hasProfile && !computed.hasRecommendations && (
            <div className="dashboard-empty-state">
              <FaRobot />
              <div>
                <h2>Generate your AI recommendations</h2>
                <p>
                  Your profile is ready. Generate recommendations to populate
                  the dashboard with careers, charts, skill gaps, and resources.
                </p>
              </div>
              <button
                type="button"
                onClick={handleGenerateRecommendations}
                disabled={generating}
              >
                {generating ? "Generating..." : "Generate Recommendations"}
              </button>
            </div>
          )}

          <div className="summary-grid">
            <motion.div className="summary-card" whileHover={{ y: -7 }}>
              <div className="summary-top">
                <span className="icon blue">
                  <FaChartLine />
                </span>
                <small>Live</small>
              </div>
              <p>Career Match Score</p>
              <h2>{computed.matchScore || 0}%</h2>
            </motion.div>

            <motion.div className="summary-card" whileHover={{ y: -7 }}>
              <div className="summary-top">
                <span className="icon purple">
                  <FaRoute />
                </span>
                <small>On Track</small>
              </div>
              <p>Roadmap Progress</p>
              <h2>{computed.roadmapProgress}%</h2>
              <div className="mini-progress">
                <span style={{ width: `${computed.roadmapProgress}%` }}></span>
              </div>
            </motion.div>

            <motion.div className="summary-card" whileHover={{ y: -7 }}>
              <div className="summary-top">
                <span className="icon green">
                  <FaCheck />
                </span>
                <small>Target: {computed.totalSkills}</small>
              </div>
              <p>Skills Completed</p>
              <h2>
                {computed.completedSkills}/{computed.totalSkills}
              </h2>
            </motion.div>

            <motion.div className="summary-card" whileHover={{ y: -7 }}>
              <div className="summary-top">
                <span className="icon cyan">
                  <FaGraduationCap />
                </span>
                <small>{computed.profileCompletion}% Profile</small>
              </div>
              <p>Learning Hours This Week</p>
              <h2>{computed.learningHours.toFixed(1)}h</h2>
            </motion.div>
          </div>

          <div className="analytics-grid">
            <motion.div
              className="ai-insight-card"
              initial={{ opacity: 0, x: -24 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div className="card-heading">
                <div>
                  <span className="ai-chip">Generated by AI</span>
                  <h2>Your Path to Excellence</h2>
                </div>
                <Link to="/recommendations">Refine Analysis</Link>
              </div>

              <div className="ai-insight-body">
                <div>
                  <p>
                    {computed.hasRecommendations ? (
                      <>
                        Based on your academic profile, interests, and skill
                        performance, <strong>{computed.aiCareerTitle}</strong> is
                        currently your strongest career path. Improving{" "}
                        <strong>
                          {computed.missingSkills.slice(0, 3).join(", ") ||
                            "your missing skills"}
                        </strong>{" "}
                        will increase your career readiness.
                      </>
                    ) : (
                      <>
                        Complete your profile and generate AI recommendations to
                        receive a career path, roadmap, and skill priorities.
                      </>
                    )}
                  </p>

                  <div className="insight-mini-grid">
                    <div>
                      <small>Priority Focus</small>
                      <div className="tag-list">
                        {(computed.missingSkills.length
                          ? computed.missingSkills
                          : ["Profile Skills", "Career Planning"]
                        )
                          .slice(0, 3)
                          .map((skill) => (
                            <span key={skill}>{skill}</span>
                          ))}
                      </div>
                    </div>

                    <div>
                      <small>Best Field</small>
                      <strong>{computed.aiCareerField}</strong>
                    </div>
                  </div>
                </div>

                <div className="readiness-ring">
                  <ResponsiveContainer width="100%" height={170}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: "Ready", value: computed.matchScore || 0 },
                          {
                            name: "Remaining",
                            value: 100 - (computed.matchScore || 0),
                          },
                        ]}
                        innerRadius={55}
                        outerRadius={75}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        <Cell fill="#0b67c2" />
                        <Cell fill="#e5edf7" />
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div>
                    <h3>{computed.matchScore || 0}%</h3>
                    <span>Readiness</span>
                  </div>
                </div>
              </div>
            </motion.div>

            <motion.div
              className="chart-card"
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div className="card-heading small">
                <h2>Skill Portfolio</h2>
              </div>

              <ResponsiveContainer width="100%" height={230}>
                <PieChart>
                  <Pie
                    data={computed.skillPieData}
                    innerRadius={62}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {computed.skillPieData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>

              <div className="pie-legend">
                {computed.skillPieData.map((item) => (
                  <div key={item.name}>
                    <span style={{ background: item.color }}></span>
                    <small>{item.name}</small>
                    <strong>{item.value}%</strong>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          <div className="charts-grid">
            <div className="chart-card wide">
              <h2>Career Recommendation Analysis</h2>
              <ResponsiveContainer width="100%" height={290}>
                <BarChart data={computed.careerChartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="score" radius={[10, 10, 0, 0]} fill="#0b67c2" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h2>Roadmap Growth</h2>
              <ResponsiveContainer width="100%" height={290}>
                <AreaChart data={computed.roadmapChart}>
                  <defs>
                    <linearGradient id="roadmapGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0b67c2" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#0b67c2" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="progress"
                    stroke="#0b67c2"
                    fill="url(#roadmapGradient)"
                    strokeWidth={3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card dark">
              <h2>Interest Strength</h2>
              <ResponsiveContainer width="100%" height={290}>
                <RadarChart data={computed.interestStrength}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: "#cbd5e1", fontSize: 11 }} />
                  <Radar
                    dataKey="value"
                    stroke="#22d3ee"
                    fill="#22d3ee"
                    fillOpacity={0.35}
                  />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="roadmap-card">
            <div className="card-heading">
              <h2>Your Career Roadmap</h2>
              <Link
                to={
                  computed.topRecommendation?.career_id
                    ? `/roadmap?careerId=${computed.topRecommendation.career_id}`
                    : "/roadmap"
                }
              >
                Open Roadmap
              </Link>
            </div>

            <div className="roadmap-line">
              {computed.roadmap.length ? (
                computed.roadmap.slice(0, 5).map((stage, index) => {
                  const active =
                    stage.completed || stage.is_completed || stage.progress === 100;

                  return (
                    <div className="roadmap-step" key={stage.stage_id || stage.title}>
                      <div className={active ? "done" : ""}>
                        {active ? <FaCheck /> : index + 1}
                      </div>
                      <strong>{stage.title}</strong>
                      <span>{active ? "Done" : "Upcoming"}</span>
                    </div>
                  );
                })
              ) : (
                <div className="dashboard-inline-empty">
                  No roadmap is available for the current top recommendation.
                </div>
              )}
            </div>
          </div>

          <div className="lower-grid">
            <div>
              <div className="section-title-row">
                <h2>Recommended Careers</h2>
                <Link to="/recommendations">View All Paths</Link>
              </div>

              <div className="career-list">
                {computed.recommendations.length === 0 && (
                  <div className="dashboard-inline-empty">
                    Generate recommendations to see your top career matches here.
                  </div>
                )}

                {computed.recommendations.slice(0, 3).map((item) => {
                  const title = getCareerTitle(item);

                  return (
                    <motion.div
                      className="career-card"
                      key={item.recommendation_id || title}
                      whileHover={{ scale: 1.02 }}
                    >
                      <img src={getCareerImage(title)} alt={title} />
                      <div>
                        <div className="career-card-top">
                          <h3>{title}</h3>
                          <span>{Math.round(getMatchScore(item))}% Match</span>
                        </div>
                        <p>{getCareerField(item)}</p>
                        <div className="tag-list">
                          {asArray(item?.matched_skills || item?.career?.required_skills)
                            .slice(0, 3)
                            .map((skill) => (
                              <small key={skill}>{skill}</small>
                            ))}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>

            <div className="activity-card">
              <h2>Weekly Activity</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={activityData}>
                  <XAxis dataKey="day" />
                  <Tooltip />
                  <Bar dataKey="hours" fill="#0b67c2" radius={[12, 12, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="resources-section">
            <div className="section-title-row">
              <h2>Curated Resources for You</h2>
              <Link
                to={
                  computed.topRecommendation?.career_id
                    ? `/resources?careerId=${computed.topRecommendation.career_id}`
                    : "/resources"
                }
              >
                Library
              </Link>
            </div>

            <div className="resource-grid">
              {[...computed.videos, ...computed.resources].length === 0 && (
                <div className="dashboard-inline-empty">
                  Recommended resources will appear after a top career is available.
                </div>
              )}

              {[...computed.videos, ...computed.resources].slice(0, 4).map((item, index) => (
                <motion.a
                  key={item.video_resource_id || item.resource_id || item.title || index}
                  href={item.video_url || item.url || "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="resource-card"
                  whileHover={{ y: -8 }}
                >
                  <div>
                    <img
                      src={
                        item.thumbnail_url ||
                        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=500&q=80"
                      }
                      alt={item.title}
                    />
                    <span>{item.platform || item.source || "Free Resource"}</span>
                  </div>
                  <h3>{item.title}</h3>
                  <p>{item.skill || item.difficulty || "Recommended Learning"}</p>
                </motion.a>
              ))}
            </div>
          </div>
        </section>
      </main>

    </div>
  );
}

export default Dashboard;
