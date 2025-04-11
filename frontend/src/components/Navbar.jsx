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
        <>
            <button 
                // className="menu-toggle"
                className={`menu-toggle ${menuOpen ? 'hidden' : ''}`} 
                onClick={() => setMenuOpen(!menuOpen)}
            >
                ☰
            </button>

            <nav className={menuOpen ? "active" : ""}>
                <div className="nav-top">
                    <div className="logo-container">
                        <img src={logo} alt="App Logo" className="logo" />
                        <span className="logo-text">Linguofy.ai</span>
                    </div>
                </div>
                
                <div className="nav-middle">
                    <Link to="/LandingPage" onClick={() => setMenuOpen(false)}>
                        📝 Transcription
                    </Link>
                    <Link to="/HistoryPage" onClick={() => setMenuOpen(false)}>
                        📚 History
                    </Link>
                    <Link to="/Agent" onClick={() => setMenuOpen(false)}>
                        👤 Agent
                    </Link>
                </div>
                
                <div className="nav-bottom">
                    {userID && (
                        <button className="logout-button" onClick={handleLogout}>
                            Logout
                        </button>
                    )}
                </div>
            </nav>

            {menuOpen && <div className="sidebar-overlay" onClick={() => setMenuOpen(false)}></div>}
        </>
    );
};

export default Navbar;