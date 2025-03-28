import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import logo from "../assets/logo.svg";
import "./Navbar.css";

const Navbar = () => {
    const [menuOpen, setMenuOpen] = useState(false);
    const navigate = useNavigate();
    const userID = sessionStorage.getItem("UserID");

    const handleLogout = () => {
        sessionStorage.removeItem("UserID");
        sessionStorage.removeItem("email");
        navigate("/");
        window.location.reload();
    };

    return (
        <nav>
            <div className="logo-container">
                <img src={logo} alt="App Logo" className="logo" />
                <span className="logo-text">Linguofy.ai</span>
            </div>
            {/* Menu toggle button for mobile */}
            <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>
                ☰
            </button>
            <div className={`nav-links ${menuOpen ? "active" : ""}`}>
                <Link to="/LandingPage" onClick={() => setMenuOpen(false)}>
                    Transcription
                </Link>
                <Link to="/HistoryPage" onClick={() => setMenuOpen(false)}>
                    History
                </Link>
                <Link to="/Agent" onClick={() => setMenuOpen(false)}>
                    Agent
                </Link>
                {userID && (
                    <button className="logout-button" onClick={handleLogout}>
                        Logout
                    </button>
                )}
            </div>
        </nav>
    );
};

export default Navbar;
