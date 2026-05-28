import React, { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      await api.post("/signup", { email, password });
      setMsg("Signup successful! Redirecting to login...");
      setIsSuccess(true);
      setTimeout(() => navigate("/login"), 1500);
    } catch (error) {
      setMsg(error.response?.data?.detail || "Signup failed");
      setIsSuccess(false);
    }
  };

  return (
    <form onSubmit={handleSignup} className="form-container">
      <h2>Signup</h2>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit" className="btn btn-green">Signup</button>
      {msg && (
        <p className={`message ${isSuccess ? "success" : ""}`}>
          {msg}
        </p>
      )}
    </form>
  );
}
