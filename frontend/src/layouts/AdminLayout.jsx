import { NavLink } from "react-router-dom";

const adminLinks = [
  ["/admin", "Dashboard"],
  ["/admin/users", "Manage Users"],
  ["/admin/careers", "Manage Careers"],
  ["/admin/roadmaps", "Manage Roadmaps"],
  ["/admin/resources", "Manage Resources"],
  ["/admin/reports", "Reports"],
  ["/dashboard", "Student App"],
];

export default function AdminLayout({ children }) {
  return (
    <div className="sidebar-layout">
      <aside className="sidebar">
        <div className="logo">Admin Panel</div>
        <nav aria-label="Admin navigation">
          {adminLinks.map(([to, name]) => (
            <NavLink key={to} to={to} end>{name}</NavLink>
          ))}
        </nav>
      </aside>
      <main className="page">{children}</main>
    </div>
  );
}
