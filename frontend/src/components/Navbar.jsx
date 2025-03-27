import { Link, useNavigate } from "react-router-dom";
import logo from "../assets/logo.svg";
import "./Navbar.css";

const Navbar = () => {
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
            <div className="nav-links">
                <Link to="/LandingPage">Transcription</Link>
                <Link to="/HistoryPage">History</Link>
            </div>
            {userID && <button className="logout-button" onClick={handleLogout}>Logout</button>}
        </nav>
    );
};

export default Navbar;