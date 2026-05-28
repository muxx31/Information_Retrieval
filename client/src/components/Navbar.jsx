import React from "react";
import { Link, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <nav style={navStyle}>
      <div style={logoStyle}>GenAI Q&A</div>
      <div style={linkContainer}>
        <Link style={linkStyle} to="/">
          Home
        </Link>
        {!token && (
          <>
            <Link style={linkStyle} to="/login">
              Login
            </Link>
            <Link style={linkStyle} to="/signup">
              Signup
            </Link>
          </>
        )}
        {token && (
          <>
            <button onClick={logout} style={logoutBtnStyle}>
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
}

const navStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "1rem 2rem",
  backgroundColor: "#007bff",
  color: "white",
  boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
};

const logoStyle = {
  fontWeight: "bold",
  fontSize: "1.5rem",
};

const linkContainer = {
  display: "flex",
  gap: "1.5rem",
  alignItems: "center",
};

const linkStyle = {
  color: "white",
  textDecoration: "none",
  fontWeight: "500",
};

const logoutBtnStyle = {
  backgroundColor: "#dc3545",
  border: "none",
  padding: "0.4rem 1rem",
  borderRadius: "5px",
  color: "white",
  cursor: "pointer",
  fontWeight: "600",
};
