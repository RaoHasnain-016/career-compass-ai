import { get, post } from "./api";

export const STUDENT_NOTIFICATIONS_CHANGED = "career-compass:notifications-changed";

export function notifyStudentNotificationsChanged() {
  window.dispatchEvent(new Event(STUDENT_NOTIFICATIONS_CHANGED));
}

export const getStudentNotifications = () => get("/student-updates/notifications");

export const markStudentNotificationsRead = (ids) =>
  post("/student-updates/notifications/read", { ids });

export const getUniversitySuggestions = () => get("/student-updates/universities");
