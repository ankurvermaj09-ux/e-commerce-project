import { useState } from "react";
import api from "./api";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const submit = async () => {
    if (!email) {
      alert("Enter an email address");
      return;
    }
    if (password.length < 5) {
      alert("Password must be at least 6 characters");
      return;
    }

    try {
      await api.post("/register", { email, password });
      alert("Account created successfully");
      navigate("/login", { state: { email } });
    } catch (error) {
      const errorMessage = error.response?.data?.detail || "An unexpected error occurred";
      alert(errorMessage);
    }
  };

  return (
    <div className="frontend-header">
      <h2>Register your account to login</h2>
      <input
        type="email"
        placeholder="Enter your email"
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="password"
        placeholder="Enter your password"
        onChange={(e) => setPassword(e.target.value)}
      />
      <button className="login-btn" onClick={submit}>
        Create Account
      </button>
    </div>
  );
}