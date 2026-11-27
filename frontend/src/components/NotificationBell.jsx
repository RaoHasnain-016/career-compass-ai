import { useEffect, useId, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { FaArrowRight, FaBell } from "react-icons/fa";
import useStudentNotifications from "../hooks/useStudentNotifications";
import NotificationItems, { NotificationStatus } from "./NotificationItems";
import "../styles/student-updates.css";

export default function NotificationBell() {
  const [expanded, setExpanded] = useState(false);
  const panelId = useId();
  const bell = useRef(null);
  const container = useRef(null);
  const notifications = useStudentNotifications();
  const { data, loading, error, reading, readError, markRead, refresh, refreshOnOpen } = notifications;
  const unread = data?.unread_count || 0;
  const items = data?.items.slice(0, 4) || [];

  useEffect(() => {
    if (!expanded) return undefined;

    function closeOnClick(event) {
      if (!container.current?.contains(event.target)) setExpanded(false);
    }
    function closeOnEscape(event) {
      if (event.key !== "Escape") return;
      setExpanded(false);
      bell.current?.focus();
    }

    document.addEventListener("pointerdown", closeOnClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [expanded]);

  return (
    <div className="student-notification" ref={container}>
      <button
        ref={bell}
        className="student-bell-button"
        type="button"
        aria-label={unread ? `Notifications, ${unread} unread` : "Notifications"}
        aria-controls={panelId}
        aria-expanded={expanded}
        onClick={() => {
          if (!expanded) refreshOnOpen();
          setExpanded(!expanded);
        }}
      >
        <FaBell aria-hidden="true" />
        {unread > 0 && <span className="student-bell-count" aria-hidden="true">{unread > 99 ? "99+" : unread}</span>}
      </button>
      {expanded && (
        <section className="student-bell-panel" id={panelId} aria-label="Recent notifications">
          <div className="student-bell-heading">
            <h2>Notifications</h2>
            <button type="button" className="student-update-text-button" disabled={loading} onClick={() => { void refresh(); }}>
              Refresh
            </button>
          </div>
          <NotificationStatus data={data} loading={loading} error={error} />
          {readError && <p className="student-updates-status warning" role="alert">{readError}</p>}
          {data && !items.length && <p className="student-updates-status">No updates for your profile yet.</p>}
          <NotificationItems items={items} compact reading={reading} onRead={markRead} />
          <Link className="student-bell-footer" to="/notifications" onClick={() => setExpanded(false)}>
            Open notification inbox <FaArrowRight aria-hidden="true" />
          </Link>
        </section>
      )}
    </div>
  );
}
