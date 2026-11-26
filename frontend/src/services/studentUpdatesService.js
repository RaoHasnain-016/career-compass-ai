import { get, post } from "./api";

export const getStudentNotifications = () => get("/student-updates/notifications");

export const markStudentNotificationsRead = (ids) =>
  post("/student-updates/notifications/read", { ids });

export const getUniversitySuggestions = () => get("/student-updates/universities");
