import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { FaBookOpen, FaExternalLinkAlt, FaFilter, FaRobot, FaSearch } from "react-icons/fa";
import StudentLayout from "../layouts/StudentLayout";
import { getRecommendedResources, getRecommendedVideos } from "../services/resourceService";
import { getTopRecommendedCareerId } from "../services/roadmapService";
import "../styles/resources-page.css";

function normalizeItem(item, type) {
  return {
    id: item.resource_id || item.video_resource_id || item.youtube_video_id || item.title,
    title: item.title || "Learning Resource",
    source: item.platform || item.source || item.channel_title || "Resource",
    url: item.url || item.video_url || "#",
    skill: item.skill || "Career Skill",
    difficulty: item.difficulty || "Beginner",
    type,
    thumbnail: item.thumbnail_url || "",
    description: item.description || "",
  };
}

export default function LearningResources() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const requestedCareerId = searchParams.get("careerId") || location.state?.careerId || "";

  const [career, setCareer] = useState(null);
  const [items, setItems] = useState([]);
  const [missingSkills, setMissingSkills] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [difficulty, setDifficulty] = useState("All");
  const [source, setSource] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadResources() {
      try {
        setLoading(true);
        setError("");

        const careerId = requestedCareerId || (await getTopRecommendedCareerId());

        if (!careerId) {
          if (active) {
            setCareer(null);
            setItems([]);
          }
          return;
        }

        const [resourceResult, videoResult] = await Promise.allSettled([
          getRecommendedResources(careerId),
          getRecommendedVideos(careerId),
        ]);

        const resourceResponse =
          resourceResult.status === "fulfilled"
            ? resourceResult.value
            : { career: null, resources: [], missingSkills: [] };
        const videoResponse =
          videoResult.status === "fulfilled"
            ? videoResult.value
            : { career: null, videos: [], missingSkills: [] };

        if (active) {
          if (resourceResult.status === "rejected" && videoResult.status === "rejected") {
            throw resourceResult.reason || videoResult.reason;
          }

          setCareer(resourceResponse.career || videoResponse.career || null);
          setMissingSkills(resourceResponse.missingSkills || videoResponse.missingSkills || []);
          setItems([
            ...resourceResponse.resources.map((item) => normalizeItem(item, "Article/Course")),
            ...videoResponse.videos.map((item) => normalizeItem(item, "Video")),
          ]);
        }
      } catch (error) {
        console.error(error);

        if (active) {
          setError(error.message || "Resources could not be loaded.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadResources();

    return () => {
      active = false;
    };
  }, [requestedCareerId]);

  const sources = useMemo(() => ["All", ...new Set(items.map((item) => item.source).filter(Boolean))], [items]);
  const difficulties = useMemo(() => ["All", ...new Set(items.map((item) => item.difficulty).filter(Boolean))], [items]);

  const filteredItems = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return items.filter((item) => {
      const matchesQuery =
        !query ||
        [item.title, item.skill, item.source, item.description]
          .join(" ")
          .toLowerCase()
          .includes(query);
      const matchesDifficulty = difficulty === "All" || item.difficulty === difficulty;
      const matchesSource = source === "All" || item.source === source;

      return matchesQuery && matchesDifficulty && matchesSource;
    });
  }, [difficulty, items, searchQuery, source]);

  if (loading) {
    return (
      <StudentLayout>
        <div className="cc-loading">
          <div className="cc-loader">
            <FaBookOpen />
          </div>
          <h2>Curating resources...</h2>
          <p>Finding free learning resources and videos for your top career path.</p>
        </div>
      </StudentLayout>
    );
  }

  if (!career && items.length === 0 && !error) {
    return (
      <StudentLayout>
        <div className="cc-empty">
          <FaRobot />
          <h2>No career selected</h2>
          <p>Generate recommendations first so resources can be matched to your skill gaps.</p>
          <Link className="cc-btn" to="/recommendations">
            Open Recommendations
          </Link>
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout className="resources-page">
      <header className="cc-page-header">
        <div>
          <h1>Learning Resources</h1>
          <p>
            Free resources and videos matched to {career?.title || "your selected career"}.
          </p>
        </div>
        <Link className="cc-btn secondary" to="/recommendations">
          Change Career
        </Link>
      </header>

      {error && <div className="resources-error">{error}</div>}

      <section className="resource-toolbar">
        <div className="resource-search">
          <FaSearch />
          <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search skill, source, resource..." />
        </div>
        <label>
          <FaFilter />
          <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
            {difficulties.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Source
          <select value={source} onChange={(event) => setSource(event.target.value)}>
            {sources.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
      </section>

      {missingSkills.length > 0 && (
        <section className="cc-card resource-gap-card">
          <h2>Skill Gaps Covered</h2>
          <div className="cc-chip-list">
            {missingSkills.map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </section>
      )}

      {filteredItems.length === 0 ? (
        <div className="cc-empty">
          <FaBookOpen />
          <h2>No resources found</h2>
          <p>Try a different search term or filter combination.</p>
        </div>
      ) : (
        <div className="resource-card-grid">
          {filteredItems.map((item, index) => (
            <motion.a
              key={`${item.id}-${index}`}
              className="resource-result-card"
              href={item.url}
              target="_blank"
              rel="noreferrer"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.04 }}
            >
              <div className="resource-thumb">
                {item.thumbnail ? <img src={item.thumbnail} alt={item.title} /> : <FaBookOpen />}
                <span>{item.type}</span>
              </div>
              <div>
                <small>{item.source}</small>
                <h2>{item.title}</h2>
                <p>{item.skill} / {item.difficulty}</p>
              </div>
              <FaExternalLinkAlt />
            </motion.a>
          ))}
        </div>
      )}
    </StudentLayout>
  );
}
