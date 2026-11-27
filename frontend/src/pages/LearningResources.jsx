import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { FaBookOpen, FaExternalLinkAlt, FaPlayCircle, FaRobot, FaSearch } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { getRecommendedResources, getRecommendedVideos } from "../services/resourceService";
import { getTopRecommendedCareerId } from "../services/roadmapService";
import "../styles/resources-page.css";

function normalizeItem(item, type) {
  return {
    id: item.resource_id || item.video_resource_id || item.youtube_video_id || item.title,
    title: item.title || "Learning Resource",
    source: item.channel_title || item.platform || item.source || "Resource",
    url: item.url || item.video_url || "#",
    skill: item.skill || "Career Skill",
    difficulty: item.difficulty || "Beginner",
    type,
    starter: item.source_type === "starter",
    thumbnail: item.thumbnail_url || "",
    description: item.description || "",
  };
}

function ResourceCards({ items }) {
  if (!items.length) return null;

  return (
    <div className="resource-card-grid">
      {items.map((item) => (
        <a key={item.id} className="resource-result-card" href={item.url} target="_blank" rel="noreferrer">
          <div className="resource-thumb">
            {item.type === "Video" ? <FaPlayCircle aria-hidden="true" /> : <FaBookOpen aria-hidden="true" />}
            {item.thumbnail && (
              <img
                src={item.thumbnail}
                alt=""
                loading="lazy"
                decoding="async"
                onError={(event) => { event.currentTarget.hidden = true; }}
              />
            )}
            <span>{item.starter ? "Starter lesson" : item.type}</span>
          </div>
          <div>
            <small>{item.source}</small>
            <h3>{item.title}</h3>
            <p>{item.skill} · {item.difficulty}</p>
          </div>
          <FaExternalLinkAlt aria-hidden="true" />
        </a>
      ))}
    </div>
  );
}

export default function LearningResources() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const requestedCareerId = searchParams.get("careerId") || location.state?.careerId || "";

  const [resources, setResources] = useState(null);
  const [videos, setVideos] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [difficulty, setDifficulty] = useState("All");
  const [source, setSource] = useState("All");
  const [loading, setLoading] = useState(true);
  const [videoLoading, setVideoLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setResources(null);
    setVideos(null);
    setSource("All");
    setDifficulty("All");
    setLoading(true);
    setVideoLoading(false);
    setError("");

    async function loadResources() {
      try {
        const careerId = requestedCareerId || (await getTopRecommendedCareerId());
        if (!active || !careerId) return;
        setVideoLoading(true);

        const results = await Promise.allSettled([
          getRecommendedResources(careerId).then((data) => {
            if (active) setResources(data);
          }),
          getRecommendedVideos(careerId).then((data) => {
            if (active) setVideos(data);
          }).finally(() => {
            if (active) setVideoLoading(false);
          }),
        ]);
        if (results.every((result) => result.status === "rejected")) {
          throw results[0].reason;
        }
      } catch (failure) {
        if (active) setError(failure?.message || "Resources could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadResources();
    return () => { active = false; };
  }, [requestedCareerId]);

  const career = resources?.career || videos?.career;
  const missingSkills = resources?.missingSkills || videos?.missingSkills || [];
  const requiredSkills = resources?.requiredSkills || videos?.requiredSkills || [];
  const videoTopics = [...new Set([...missingSkills, ...requiredSkills].map((skill) => String(skill || "").trim().toLowerCase()))]
    .filter(Boolean).slice(0, 5);
  const items = useMemo(() => [
    ...(videos?.videos || []).map((item) => normalizeItem(item, "Video")),
    ...(resources?.resources || []).map((item) => normalizeItem(item, "Article or course")),
  ], [resources, videos]);

  const sources = ["All", ...new Set(items.map((item) => item.source))];
  const difficulties = ["All", ...new Set(items.map((item) => item.difficulty))];
  const query = searchQuery.trim().toLowerCase();
  const filteredItems = items.filter((item) =>
    (difficulty === "All" || item.difficulty === difficulty) &&
    (source === "All" || item.source === source) &&
    [item.title, item.skill, item.source, item.description].join(" ").toLowerCase().includes(query)
  );
  const videoItems = filteredItems.filter((item) => item.type === "Video");
  const courseItems = filteredItems.filter((item) => item.type !== "Video");

  if (loading && !career) {
    return (
      <StudentLayout>
        <div className="cc-loading">
          <div className="cc-loader"><FaBookOpen aria-hidden="true" /></div>
          <h2>Loading learning resources…</h2>
        </div>
      </StudentLayout>
    );
  }

  if (!career && !error) {
    return (
      <StudentLayout>
        <div className="cc-empty">
          <FaRobot aria-hidden="true" />
          <h2>No career selected</h2>
          <p>Generate recommendations first so resources can be matched to your skill gaps.</p>
          <Link className="cc-btn" to="/recommendations">Open Recommendations</Link>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout className="resources-page">
      <header className="cc-page-header">
        <div>
          <h1>Learning Resources</h1>
          <p>Free resources and videos matched to {career?.title || "your selected career"}.</p>
        </div>
        <Link className="cc-btn secondary" to="/recommendations">Change Career</Link>
      </header>

      {error && <div className="resources-error" role="alert">{error}</div>}

      {career && (
        <>
          <section className="resource-toolbar" aria-label="Filter learning resources">
            <div className="resource-search">
              <FaSearch aria-hidden="true" />
              <input
                aria-label="Search learning resources"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search skill, source, resource..."
              />
            </div>
            <label>
              Level
              <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
                {difficulties.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label>
              Source
              <select value={source} onChange={(event) => setSource(event.target.value)}>
                {sources.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
          </section>

          {missingSkills.length > 0 && (
            <section className="cc-card resource-gap-card">
              <h2>Skills to build</h2>
              <div className="cc-chip-list">
                {missingSkills.map((skill) => <span key={skill}>{skill}</span>)}
              </div>
            </section>
          )}

          <section className="resource-section" aria-labelledby="video-lessons-heading">
            <h2 id="video-lessons-heading"><FaPlayCircle aria-hidden="true" /> Video lessons</h2>
            <ResourceCards items={videoItems} />
            {videoLoading && <p className="resource-section-note" role="status">Looking up videos for this career…</p>}
            {!videoLoading && !videoItems.length && (
              <p className="resource-section-note">
                {videos?.videos.length ? "No videos match your filters." : "No video recommendations are available right now."}
              </p>
            )}
            <div className="resource-topic-list">
              <h3>Search YouTube by topic</h3>
              <ul>
                {(videoTopics.length ? videoTopics : [career.title]).map((topic) => (
                  <li key={topic}>
                    <a
                      href={`https://www.youtube.com/results?search_query=${encodeURIComponent(
                        topic === career.title ? `${topic} career introduction` : `${topic} beginner tutorial ${career.title}`
                      )}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {topic} <FaExternalLinkAlt aria-hidden="true" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section className="resource-section" aria-labelledby="course-heading">
            <h2 id="course-heading"><FaBookOpen aria-hidden="true" /> Articles and courses</h2>
            {courseItems.length ? <ResourceCards items={courseItems} /> : (
              <p className="resource-section-note">
                {loading && !resources ? "Loading articles and courses…" : "No articles or courses match this view."}
              </p>
            )}
          </section>
        </>
      )}
    </StudentLayout>
  );
}
