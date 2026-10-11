import { get } from "./api";
import { getMyRecommendations } from "./recommendationService";
import { getStudentProfile } from "./profileService";

export async function getRoadmap(careerId) {
  if (!careerId) return { career: null, roadmap: [] };

  const response = await get(`/roadmaps/${careerId}`, { auth: false });

  return {
    career: response?.career || null,
    roadmap: Array.isArray(response?.roadmap)
      ? response.roadmap
      : Array.isArray(response)
      ? response
      : [],
  };
}

export async function getTopRecommendedCareerId() {
  const [recommendations, profile] = await Promise.all([
    getMyRecommendations(),
    getStudentProfile().catch(() => null),
  ]);
  if (profile?.selected_career_id) return profile.selected_career_id;
  return recommendations[0]?.career_id || recommendations[0]?.career?.career_id || "";
}
