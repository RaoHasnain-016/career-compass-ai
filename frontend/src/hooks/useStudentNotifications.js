import { useCallback, useEffect, useRef, useState } from "react";
import { getStudentNotifications, markStudentNotificationsRead } from "../services/studentUpdatesService";

const REFRESH_INTERVAL = 5 * 60 * 1000;

export default function useStudentNotifications() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reading, setReading] = useState(false);
  const [readError, setReadError] = useState("");
  const active = useRef(false);
  const loadingRequest = useRef(null);
  const readingRequest = useRef(false);
  const readIds = useRef(new Set());
  const lastCheck = useRef(0);

  const refresh = useCallback(async () => {
    if (loadingRequest.current) return;
    lastCheck.current = Date.now();
    const request = getStudentNotifications();
    loadingRequest.current = request;
    setLoading(true);
    setError("");
    try {
      const response = await request;
      if (!active.current || loadingRequest.current !== request) return;
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
      if (active.current && loadingRequest.current === request) {
        setError("Notifications could not be refreshed. Please try again.");
      }
    } finally {
      if (active.current && loadingRequest.current === request) {
        loadingRequest.current = null;
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    active.current = true;
    void refresh();
    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible" && Date.now() - lastCheck.current >= REFRESH_INTERVAL) {
        void refresh();
      }
    };
    const timer = window.setInterval(refreshWhenVisible, REFRESH_INTERVAL);
    document.addEventListener("visibilitychange", refreshWhenVisible);
    return () => {
      active.current = false;
      loadingRequest.current = null;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
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
      const confirmed = Array.isArray(result?.read_ids) ? result.read_ids : ids;
      for (const id of confirmed) readIds.current.add(id);
      setData((current) => {
        if (!current) return current;
        const changed = new Set(confirmed);
        const items = current.items.map((item) => changed.has(item.id) ? { ...item, read: true } : item);
        const unreadCount = Number.isInteger(result?.unread_count)
          ? result.unread_count
          : items.filter((item) => !item.read).length;
        return { ...current, items, unread_count: unreadCount };
      });
    } catch {
      if (active.current) setReadError("Read status could not be saved. Please try again.");
    } finally {
      readingRequest.current = false;
      if (active.current) setReading(false);
    }
  }

  return { data, loading, error, refresh, reading, readError, markRead };
}
