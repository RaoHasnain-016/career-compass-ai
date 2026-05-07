import { get } from "./api";
import { normalizeRecommendations } from "./recommendationService";

function normalizeList(response, keys = []) {
  if (!response) return [];
  if (Array.isArray(response)) return response;

  for (const key of keys) {
    if (Array.isArray(response[key])) return response[key];
  }

  return [];
}

async function getOptional(path, fallback = null, options = {}) {
  try {
    return await get(path, options);
  } catch (error) {
    if (error.status === 404) return fallback;
    throw error;
  }
}

export async function getDashboardData() {
  const [profile, recommendationResponse, savedCareersResponse] =
    await Promise.all([
      getOptional("/student/profile", null),
      getOptional("/recommendations/me", { recommendations: [] }),
      getOptional("/saved-careers", { saved_careers: [] }),
    ]);

  const recommendations = normalizeRecommendations(recommendationResponse);
  const topRecommendation = recommendations[0] || null;
  const careerId = topRecommendation?.career_id || topRecommendation?.career?.career_id;

  let roadmapResponse = { roadmap: [] };
  let resourcesResponse = { recommended_resources: [] };
  let videosResponse = { video_courses: [] };

  if (careerId) {
    [roadmapResponse, resourcesResponse, videosResponse] = await Promise.all([
      getOptional(`/roadmaps/${careerId}`, { roadmap: [] }, { auth: false }),
      getOptional(`/resources/recommended/${careerId}`, {
        recommended_resources: [],
      }),
      getOptional(`/resources/videos/${careerId}`, { video_courses: [] }),
    ]);
  }

  return {
    profile,
    recommendations,
    topRecommendation,
    career: roadmapResponse?.career || topRecommendation || null,
    roadmap: normalizeList(roadmapResponse, ["roadmap", "roadmap_stages", "stages", "data"]),
    resources: normalizeList(resourcesResponse, [
      "recommended_resources",
      "resources",
      "data",
    ]),
    videos: normalizeList(videosResponse, ["video_courses", "videos", "data"]),
    savedCareers: normalizeList(savedCareersResponse, [
      "saved_careers",
      "savedCareers",
      "data",
    ]),
  };
}
