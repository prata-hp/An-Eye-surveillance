import { useState } from "react";
import { useNavigate } from "react-router-dom";

import API from "../services/api";


function Login() {
  const [error, setError] = useState("");
  const [password, setPassword] = useState("password123");
  const [username, setUsername] = useState("operator1");
  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    try {
      const response = await API.post("/login", {
        username,
        password,
      });

      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("role", response.data.role);
      localStorage.setItem("city", response.data.city);
      localStorage.setItem("precinct", response.data.precinct);
      localStorage.setItem("username", username);

      navigate("/");
    } catch (requestError) {
      console.error(requestError);
      setError("Invalid username or password.");
    }
  }

  return (
    <main className="login-page">
      <form className="login-panel" onSubmit={handleSubmit}>
        <div>
          <p>AN-EYE Secure Access</p>
          <h1>Operator Login</h1>
        </div>

        <label>
          Username
          <input
            autoComplete="username"
            onChange={(event) => setUsername(event.target.value)}
            value={username}
          />
        </label>

        <label>
          Password
          <input
            autoComplete="current-password"
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            value={password}
          />
        </label>

        {error && <div className="login-error">{error}</div>}

        <button type="submit">Sign In</button>
      </form>
    </main>
  );
}


export default Login;
