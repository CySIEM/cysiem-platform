import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Login.css";

const Login = () => {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // If already logged in, go to Dashboard
  useEffect(() => {
    const user = localStorage.getItem("user");

    if (user) {
      navigate("/");
    }
  }, [navigate]);

  const handleLogin = (e) => {
    e.preventDefault();

    const user = username.trim();
    const pass = password.trim();

    if (user === "admin" && pass === "admin123") {
      localStorage.setItem("user", "admin");

      alert("Login Successful!");

      navigate("/");
    } else {
      alert("Invalid Username or Password");
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">

        <h1>🛡️ CySIEM Platform</h1>

        <h2>Admin Login</h2>

        <form onSubmit={handleLogin}>

          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />

          <button type="submit">
            Login
          </button>

        </form>

        <p className="login-info">
          <strong>Demo Credentials</strong>
          <br />
          Username: <b>admin</b>
          <br />
          Password: <b>admin123</b>
        </p>

      </div>
    </div>
  );
};

export default Login;