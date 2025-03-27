import { Navigate } from "react-router-dom";
import Navbar from "./Navbar";

const ProtectedRoute = ({ children }) => {
    const userID = sessionStorage.getItem("UserID");

    if (!userID) {
        return <Navigate to="/" />;
    }

    return (
        <>
            <Navbar />
            <div style={{height: "calc(100vh - 80px)", overflowY: "auto" }}>
                {children}
            </div>

        </>
    );
};

export default ProtectedRoute;