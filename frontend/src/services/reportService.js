function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  }[character]));
}

export function downloadCareerReport({ profile, recommendations, selectedCareerId, name }) {
  const selected = recommendations.find((item) => (item.career_id || item?.career?.career_id) === selectedCareerId) || recommendations[0];
  const rows = recommendations.map((item, index) => `<tr><td>${index + 1}</td><td>${escapeHtml(item.title)}</td><td>${escapeHtml(item.field)}</td><td>${Math.round(Number(item.match_score || 0))}%</td><td>${escapeHtml(item.improvement_advice || "Continue building relevant skills.")}</td></tr>`).join("");
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>Career Compass Report</title><style>body{font-family:Arial,sans-serif;color:#172033;max-width:900px;margin:48px auto;line-height:1.55}h1{color:#0b67c2}h2{margin-top:34px;color:#1e3a5f}.badge{display:inline-block;padding:7px 12px;border-radius:999px;background:#eaf4ff;color:#0b67c2;font-weight:bold}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-bottom:1px solid #dbe4ef;text-align:left;vertical-align:top}th{background:#f3f8ff}</style></head><body><h1>Career Compass AI</h1><p>Personalized Career Guidance Report</p><p><strong>Student:</strong> ${escapeHtml(name || "Student")}<br><strong>Country:</strong> ${escapeHtml(profile?.country || "Not added")}<br><strong>Academic level:</strong> ${escapeHtml(profile?.academic_level || "Not added")}<br><strong>Generated:</strong> ${new Date().toLocaleDateString()}</p><h2>Selected Career Path</h2><p class="badge">${escapeHtml(selected?.title || "Choose a career")}</p><p>${escapeHtml(selected?.overview || selected?.explanation || "Select a recommendation to receive a focused path.")}</p><h2>Career Recommendations</h2><table><thead><tr><th>#</th><th>Career</th><th>Field</th><th>Match</th><th>Next step</th></tr></thead><tbody>${rows}</tbody></table><h2>Profile strengths</h2><p>${escapeHtml((profile?.skills || []).join(", ") || "Not added")}</p></body></html>`;
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "career-compass-report.html";
  link.click();
  URL.revokeObjectURL(url);
}
