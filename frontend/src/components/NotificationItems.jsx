import { Link } from "react-router-dom";
import { FaBell, FaBookOpen, FaGraduationCap, FaRegCheckCircle } from "react-icons/fa";
import StudentUpdateLink from "./StudentUpdateLink";

const categories = {
  career_news: { title: "Career news", icon: FaBookOpen },
  news: { title: "Career news", icon: FaBookOpen },
  admissions: { title: "Admissions", icon: FaGraduationCap },
  catalog: { title: "Career catalog", icon: FaBookOpen },
  university: { title: "Study options", icon: FaGraduationCap },
  system: { title: "App update", icon: FaBell },
  app_update: { title: "App update", icon: FaBell },
  platform: { title: "App update", icon: FaBell },
  profile: { title: "Profile", icon: FaBell },
  recommendation: { title: "Recommendations", icon: FaBell },
  recommendations: { title: "Recommendations", icon: FaBell },
};

export function formatUpdateDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export function NotificationStatus({ data, loading, error }) {
  if (error) return <p className="student-updates-status warning" role="alert">{error}</p>;
  if (loading && !data) return <p className="student-updates-status" role="status">Loading notifications…</p>;
  if (data?.feed_status === "stale") {
    return <p className="student-updates-status warning">Some sources could not be reached. Recent updates from those sources may be cached.</p>;
  }
  if (data?.feed_status === "unavailable") {
    return <p className="student-updates-status warning">Live career news is temporarily unavailable.</p>;
  }
  if (data?.feed_status === "profile_needed") {
    return (
      <p className="student-updates-status">
        <Link className="student-update-link" to="/profile-setup">Complete your profile</Link> to see career news that matches your education stage and interests.
      </p>
    );
  }
  if (data?.feed_status === "live" && data.feed_sources?.some((source) => source.status === "unavailable")) {
    return <p className="student-updates-status warning">Some official sources are temporarily unavailable.</p>;
  }
  return null;
}

export default function NotificationItems({ items, compact = false, reading, onRead }) {
  if (!items.length) return null;

  return (
    <ul className={`student-notification-list${compact ? " compact" : ""}`}>
      {items.map((item) => {
        const category = categories[item.category] || categories.system;
        const Icon = category.icon;
        const published = formatUpdateDate(item.published_at);
        return (
          <li className={`student-notification-item${item.read ? "" : " unread"}`} key={item.id}>
            <div className="student-update-icon"><Icon aria-hidden="true" /></div>
            <div className="student-notification-content">
              <div className="student-update-meta">
                <span>{category.title}</span>
                {item.country && <span>{item.country}</span>}
                {published && <time dateTime={item.published_at}>{published}</time>}
                {!item.read && <span className="student-unread-label">Unread</span>}
              </div>
              <h3>{item.title}</h3>
              {!compact && item.summary && <p>{item.summary}</p>}
              {!compact && item.source && <div className="student-update-source">{item.source}</div>}
              <StudentUpdateLink
                className="student-update-link"
                url={item.url}
                label={`View update: ${item.title}`}
                onClick={() => { if (!item.read) void onRead([item.id]); }}
              >
                View update
              </StudentUpdateLink>
            </div>
            {!item.read && (
              <button
                className="student-mark-button"
                type="button"
                disabled={reading}
                aria-label={`Mark “${item.title}” as read`}
                onClick={() => { void onRead([item.id]); }}
              >
                <FaRegCheckCircle aria-hidden="true" />
              </button>
            )}
          </li>
        );
      })}
    </ul>
  );
}
