import React, { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post("/login", { email, password });
      localStorage.setItem("token", res.data.access_token);
      setMsg("Login successful!");
      setIsSuccess(true);
      setTimeout(() => navigate("/"), 1500);
    } catch (error) {
      setMsg(error.response?.data?.detail || "Login failed");
      setIsSuccess(false);
    }
  };

  return (
    <form onSubmit={handleLogin} className="form-container">
      <h2>Login</h2>
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
      <button type="submit" className="btn btn-blue">Login</button>
      {msg && (
        <p className={`message ${isSuccess ? "success" : ""}`}>
          {msg}
        </p>
      )}
    </form>
  );
}
