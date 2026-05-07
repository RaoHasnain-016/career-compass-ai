import Sidebar from "../components/Sidebar";
import "../styles/student-layout.css";

export default function StudentLayout({ children, className = "" }) {
  return (
    <div className="student-shell">
      <Sidebar />
      <main className={`student-main ${className}`}>{children}</main>
    </div>
  );
}
