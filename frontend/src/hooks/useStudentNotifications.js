import { useCallback, useEffect, useRef, useState } from "react";
import {
  getStudentNotifications,
  markStudentNotificationsRead,
  STUDENT_NOTIFICATIONS_CHANGED,
} from "../services/studentUpdatesService";

const REFRESH_INTERVAL = 5 * 60 * 1000;
const BELL_REFRESH_INTERVAL = 30 * 1000;

export default function useStudentNotifications() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reading, setReading] = useState(false);
  const [readError, setReadError] = useState("");
  const active = useRef(false);
  const loadingRequest = useRef(null);
  const refreshQueued = useRef(false);
  const readingRequest = useRef(false);
  const readIds = useRef(new Set());
  const lastCheck = useRef(0);

  const refresh = useCallback(async function requestNotifications({ queue = false } = {}) {
    if (loadingRequest.current) {
      if (queue) refreshQueued.current = true;
      return;
    }
    lastCheck.current = Date.now();
    const request = getStudentNotifications();
    loadingRequest.current = request;
    setLoading(true);
    setError("");
    try {
      const response = await request;
      if (!active.current || loadingRequest.current !== request || refreshQueued.current) return;
      if (!Array.isArray(response?.items)) throw new Error("Invalid notification response.");

      let changes = 0;
      const items = response.items.map((item) => {
        if (item.read || !readIds.current.has(item.id)) return item;
        changes += 1;
        return { ...item, read: true };
      });
      const unreadCount = Number.isInteger(response.unread_count)
        ? Math.max(0, response.unread_count - changes)
        : items.filter((item) => !item.read).length;
      setData({ ...response, items, unread_count: unreadCount });
    } catch {
      if (active.current && loadingRequest.current === request && !refreshQueued.current) {
        setError("Notifications could not be refreshed. Please try again.");
      }
    } finally {
      if (active.current && loadingRequest.current === request) {
        loadingRequest.current = null;
        if (refreshQueued.current) {
          refreshQueued.current = false;
          void requestNotifications();
        } else {
          setLoading(false);
        }
      }
    }
  }, []);

  const refreshOnOpen = useCallback(() => {
    if (Date.now() - lastCheck.current >= BELL_REFRESH_INTERVAL) void refresh();
  }, [refresh]);

  useEffect(() => {
    active.current = true;
    void refresh();
    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible" && Date.now() - lastCheck.current >= REFRESH_INTERVAL) {
        void refresh();
      }
    };
    const timer = window.setInterval(refreshWhenVisible, REFRESH_INTERVAL);
    const refreshAfterProfileChange = () => { void refresh({ queue: true }); };
    document.addEventListener("visibilitychange", refreshWhenVisible);
    window.addEventListener(STUDENT_NOTIFICATIONS_CHANGED, refreshAfterProfileChange);
    return () => {
      active.current = false;
      loadingRequest.current = null;
      refreshQueued.current = false;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
      window.removeEventListener(STUDENT_NOTIFICATIONS_CHANGED, refreshAfterProfileChange);
    };
  }, [refresh]);

  async function markRead(ids) {
    if (readingRequest.current || !ids.length) return;
    readingRequest.current = true;
    setReadError("");
    setReading(true);
    try {
      const result = await markStudentNotificationsRead(ids);
      if (!active.current) return;
      if (!Array.isArray(result?.read_ids)) throw new Error("Invalid read confirmation.");
      const confirmed = result.read_ids;
      for (const id of confirmed) readIds.current.add(id);
      setData((current) => {
        if (!current) return current;
        const changed = new Set(confirmed);
        const items = current.items.map((item) => changed.has(item.id) ? { ...item, read: true } : item);
        return { ...current, items, unread_count: items.filter((item) => !item.read).length };
      });
    } catch {
      if (active.current) setReadError("Read status could not be saved. Please try again.");
    } finally {
      readingRequest.current = false;
      if (active.current) setReading(false);
    }
  }

  return { data, loading, error, refresh, refreshOnOpen, reading, readError, markRead };
}
