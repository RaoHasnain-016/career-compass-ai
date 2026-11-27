import { Link } from "react-router-dom";
import { FaBell, FaSyncAlt } from "react-icons/fa";
import NotificationItems, { formatUpdateDate, NotificationStatus } from "../components/NotificationItems";
import useStudentNotifications from "../hooks/useStudentNotifications";
import StudentLayout from "../layouts/StudentLayout";
import "../styles/student-updates.css";

export default function Notifications() {
  const { data, loading, error, refresh, reading, readError, markRead } = useStudentNotifications();
  const unreadIds = data?.items.filter((item) => !item.read).map((item) => item.id) || [];
  const checkedAt = formatUpdateDate(data?.refreshed_at);
  const hasCareerUpdates = data?.items.some((item) => ["career_news", "admissions"].includes(item.category));

  return (
    <StudentLayout className="student-updates-page">
      <header className="cc-page-header">
        <div>
          <h1>Notifications</h1>
          <p>Career news and student updates relevant to your profile.</p>
        </div>
        <div className="cc-actions student-update-actions">
          <button className="cc-btn secondary" type="button" disabled={loading} onClick={() => { void refresh(); }}>
            <FaSyncAlt aria-hidden="true" /> Refresh
          </button>
          {unreadIds.length > 0 && (
            <button className="cc-btn" type="button" disabled={reading} onClick={() => { void markRead(unreadIds); }}>
              {reading ? "Saving…" : "Mark all as read"}
            </button>
          )}
        </div>
      </header>

      <section className="cc-card student-updates-card" aria-labelledby="inbox-heading">
        <div className="student-updates-heading">
          <h2 id="inbox-heading">Inbox</h2>
          {data && <span className="student-updates-count" aria-live="polite">{data.unread_count} unread</span>}
        </div>
        {checkedAt && <p className="student-update-source">Sources checked <time dateTime={data.refreshed_at}>{checkedAt}</time></p>}
        {data?.career_focus && <p className="student-update-source">Career focus: {data.career_focus}</p>}
        <NotificationStatus data={data} loading={loading} error={error} />
        {data?.feed_status === "live" && data.career_focus && !hasCareerUpdates && (
          <p className="student-updates-status">No recent updates from the available sources match this career and education stage.</p>
        )}
        {readError && <p className="student-updates-status warning" role="alert">{readError}</p>}
        {data && data.items.length === 0 && (
          <div className="student-updates-empty">
            <FaBell aria-hidden="true" />
            <p>No notifications match your profile yet.</p>
            <Link to="/profile-setup" className="student-update-link">Review your profile</Link>
          </div>
        )}
        {data && <NotificationItems items={data.items} reading={reading} onRead={markRead} />}
      </section>
    </StudentLayout>
  );
}
