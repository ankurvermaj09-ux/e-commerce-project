import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

export default function LoginPage({ user, login, email, setEmail, password, setPassword, loginError, SetLoginError }) {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const passedEmail = location.state?.email;
    if (passedEmail) {
      setEmail(passedEmail);
    }
  }, [location.state, setEmail]);

  return (
    <div>
      <div className="frontend-header">
        <h1>Login To start shopping</h1>
        <br />
        {!user ? (
          <div>
            <input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); SetLoginError(""); }}
              placeholder="Email"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); SetLoginError(""); }}
              placeholder="Password"
            />

            {loginError && (<p style={{ color: "red" }}>{loginError}</p>)}

            <button className="login-btn" onClick={login}>Login</button>
          </div>
        ) : (
          <div>
            <h3>Welcome {user.name}</h3>
            {user.role === "admin" && (
              <button className="admin-btn" onClick={() => navigate("/admin")}>
                Admin Dashboard
              </button>
            )}
          </div>
        )}
      </div>
      <p style={{ cursor: "pointer" }} onClick={() => navigate("/register")}>
        No account? Create a new one
      </p>
      <p style={{ cursor: "pointer" }} onClick={() => navigate("/forgot-password")}>
        Forgot Password?
      </p>
    </div>
  );
}
