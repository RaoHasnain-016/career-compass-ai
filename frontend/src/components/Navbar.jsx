import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="nav public-nav" aria-label="Site navigation">
      <Link to="/" className="logo">Career Compass AI</Link>
      <div className="public-nav-links">
        <a href="/#solutions">Features</a>
        <a href="/#how-it-works">How It Works</a>
        <Link to="/login">Login</Link>
        <Link className="btn" to="/signup">Get Started</Link>
      </div>
    </nav>
  );
}
