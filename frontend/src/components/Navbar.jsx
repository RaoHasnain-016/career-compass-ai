import { Link } from "react-router-dom";
export default function Navbar(){ return <nav className="nav"><Link to="/" className="logo">Career Compass AI</Link><div style={{display:"flex",gap:18,alignItems:"center"}}><a href="#features">Features</a><a href="#how">How It Works</a><Link to="/login">Login</Link><Link className="btn" to="/signup">Get Started</Link></div></nav> }
