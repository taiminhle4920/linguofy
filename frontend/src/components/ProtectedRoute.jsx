import { Navigate } from "react-router-dom";

const ProtectedRoute = ({ children }) => {
    const userID = sessionStorage.getItem("UserID");

    if (!userID) {
        return <Navigate to="/" />;
    }

    return children;
};

export default ProtectedRoute;