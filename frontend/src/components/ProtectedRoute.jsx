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
            {children}
        </>
    );
};

export default ProtectedRoute;