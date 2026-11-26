import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { FaGlobe, FaGraduationCap, FaLandmark, FaSyncAlt } from "react-icons/fa";
import { formatUpdateDate } from "../components/NotificationItems";
import StudentUpdateLink from "../components/StudentUpdateLink";
import StudentLayout from "../layouts/StudentLayout";
import { getUniversitySuggestions } from "../services/studentUpdatesService";
import "../styles/student-updates.css";

const verificationLabels = {
  live: "Source checked",
  verified: "Source checked",
  cached: "Previous check",
  stale: "Previous check",
  unavailable: "Source check unavailable",
  unchecked: "Source not yet checked",
};

const fieldLabels = { social_sciences: "Social sciences", technology: "Technology", data: "Data" };

function StudyOption({ option }) {
  const checked = formatUpdateDate(option.checked_at);
  const status = verificationLabels[option.verification_status];
  return (
    <li className="study-option">
      <div className="student-update-meta">
        {option.country && <span>{option.country}</span>}
        {option.level && <span>{option.level}</span>}
      </div>
      <h3>{option.institution || option.title}</h3>
      {option.institution && option.title && option.title !== option.institution && (
        <p className="study-option-program">{option.title}</p>
      )}
      {option.note && <p>{option.note}</p>}
      {status && (
        <p className="student-update-source">
          {status}{checked && <> · <time dateTime={option.checked_at}>{checked}</time></>}
        </p>
      )}
      <StudentUpdateLink
        url={option.url}
        className="student-update-link"
        label={`Open official source for ${option.institution || option.title}`}
      >
        Open official source
      </StudentUpdateLink>
    </li>
  );
}

function StudyOptionsSection({ title, icon: Icon, options, emptyText, headingId }) {
  return (
    <section className="cc-card student-updates-card" aria-labelledby={headingId}>
      <div className="student-updates-heading">
        <h2 id={headingId}><Icon aria-hidden="true" /> {title}</h2>
      </div>
      {options.length ? (
        <ul className="study-option-list">
          {options.map((option) => <StudyOption key={`${option.institution || ""}:${option.title}:${option.url}`} option={option} />)}
        </ul>
      ) : <p className="student-updates-status">{emptyText}</p>}
    </section>
  );
}

function textLines(value) {
  return (Array.isArray(value) ? value : [value]).filter((line) => typeof line === "string" && line.trim());
}

export default function Universities() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const activeRequest = useRef(null);

  const refresh = useCallback(async () => {
    const request = getUniversitySuggestions();
    activeRequest.current = request;
    setLoading(true);
    setError("");
    try {
      const response = await request;
      if (activeRequest.current !== request) return;
      if (!Array.isArray(response?.domestic) || !Array.isArray(response?.international)) {
        throw new Error("Invalid study options response.");
      }
      setData(response);
    } catch {
      if (activeRequest.current === request) setError("Study options could not be loaded. Please try again.");
    } finally {
      if (activeRequest.current === request) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    return () => { activeRequest.current = null; };
  }, [refresh]);

  const checkedAt = formatUpdateDate(data?.checked_at);
  const showPrograms = data && (
    data.domestic.length > 0 || data.international.length > 0 ||
    !["school", "exploring"].includes(data.stage)
  );

  return (
    <StudentLayout className="student-updates-page">
      <header className="cc-page-header">
        <div>
          <h1>University & study options</h1>
          <p>Explore study pathways at home and abroad based on your education stage and career interests.</p>
        </div>
        <div className="cc-actions student-update-actions">
          <button className="cc-btn secondary" type="button" disabled={loading} onClick={() => { void refresh(); }}>
            <FaSyncAlt aria-hidden="true" /> Refresh
          </button>
          <Link className="cc-btn" to="/profile-setup">Update profile</Link>
        </div>
      </header>

      {loading && !data && <p className="cc-card student-updates-status" role="status">Checking study options…</p>}
      {error && <p className="cc-card student-updates-status warning" role="alert">{error}</p>}
      {data && (
        <div className="student-study-results">
          <section className="cc-card student-updates-card" aria-labelledby="pathway-heading">
            <div className="student-updates-heading">
              <h2 id="pathway-heading"><FaGraduationCap aria-hidden="true" /> Your next study step</h2>
              {data.target_level && <span className="student-updates-count">{data.target_level}</span>}
            </div>
            {textLines(data.pathway).map((line, index) => <p className="study-pathway" key={index}>{line}</p>)}
            {data.profile_field && <p>Field: {fieldLabels[data.profile_field] || data.profile_field.replace(/^./, (letter) => letter.toUpperCase())}{data.profile_country && ` · Education system: ${data.profile_country}`}</p>}
            {textLines(data.guidance).map((line, index) => <p key={index}>{line}</p>)}
            {checkedAt && <p className="student-update-source">Sources checked <time dateTime={data.checked_at}>{checkedAt}</time></p>}
          </section>

          {showPrograms && (
            <div className="cc-grid two student-study-grid">
              <StudyOptionsSection
                title="Study in your country"
                icon={FaLandmark}
                options={data.domestic}
                emptyText="There are no matching local options in the current catalog. Check the official guides below for more paths."
                headingId="domestic-study-heading"
              />
              <StudyOptionsSection
                title="Study abroad"
                icon={FaGlobe}
                options={data.international}
                emptyText="There are no matching international options in the current catalog."
                headingId="international-study-heading"
              />
            </div>
          )}

          {data.admissions_status && data.stage !== "exploring" && (
            <section className="cc-card student-updates-card" aria-labelledby="admissions-heading">
              <div className="student-updates-heading">
                <h2 id="admissions-heading">Recent official admissions notices</h2>
              </div>
              {data.admissions_status === "stale" && <p className="student-updates-status warning">Some sources are showing a previous check.</p>}
              {data.admissions_status === "unavailable" && <p className="student-updates-status warning">Official feeds could not be refreshed.</p>}
              {data.admissions_status === "live" && !data.admissions_updates?.length && <p className="student-updates-status">No recent notices from the connected sources match your profile.</p>}
              {!!data.admissions_updates?.length && (
                <ul className="study-option-list">
                  {data.admissions_updates.map((notice) => (
                    <li className="study-option" key={notice.id}>
                      <h3>{notice.title}</h3>
                      <p className="student-update-source">{notice.source} · <time dateTime={notice.published_at}>{formatUpdateDate(notice.published_at)}</time></p>
                      {notice.summary && <p>{notice.summary}</p>}
                      <StudentUpdateLink url={notice.url} className="student-update-link">Read official notice</StudentUpdateLink>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}

          {data.sources?.length > 0 && (
            <StudyOptionsSection
              title="Official guides"
              icon={FaLandmark}
              options={data.sources}
              headingId="study-sources-heading"
            />
          )}
        </div>
      )}
    </StudentLayout>
  );
}
