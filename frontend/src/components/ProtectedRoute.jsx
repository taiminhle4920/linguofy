import { Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Navbar from "./Navbar";

const ProtectedRoute = ({ children }) => {
    const userID = sessionStorage.getItem("UserID");
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth <= 768);
        };

        window.addEventListener('resize', handleResize);
        return () => {
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    if (!userID) {
        return <Navigate to="/" />;
    }

    return (
        <div style={{ display: "flex" }}>
            <Navbar />
            <div style={{ 
                marginLeft: isMobile ? "0" : "240px", 
                flex: 1,
                transition: "margin-left 0.3s ease",
                padding: "20px"
            }}>
                {children}
            </div>
        </div>
    );
};

export default ProtectedRoute;