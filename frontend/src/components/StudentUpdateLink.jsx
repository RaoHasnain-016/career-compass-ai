import { Link } from "react-router-dom";
import { FaExternalLinkAlt } from "react-icons/fa";

export default function StudentUpdateLink({ url, children, className, label, onClick }) {
  if (typeof url !== "string" || /[\s\\]/.test(url)) return null;
  if (/^\/(?!\/)/.test(url)) {
    return <Link className={className} to={url} onClick={onClick} aria-label={label}>{children}</Link>;
  }

  let source;
  try {
    source = new URL(url);
  } catch {
    return null;
  }
  if (source.protocol !== "https:" || source.username || source.password) return null;

  return (
    <a
      className={className}
      href={source.href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      onClick={onClick}
    >
      {children} <FaExternalLinkAlt aria-hidden="true" />
    </a>
  );
}
