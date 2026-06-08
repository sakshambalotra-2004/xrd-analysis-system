import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const HARDCODED_USER = { username: "admin", password: "xrd2024" };

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const s = {
    page: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", backgroundColor: "#f3f4f6" },
    card: { background: "#ffffff", border: "0.5px solid #e5e7eb", borderRadius: "12px", padding: "2rem", width: "100%", maxWidth: "380px" },
    logoRow: { display: "flex", alignItems: "center", gap: "10px", marginBottom: "1.75rem" },
    logoIcon: { width: "36px", height: "36px", borderRadius: "8px", background: "#1B3A6B", display: "flex", alignItems: "center", justifyContent: "center" },
    heading: { fontSize: "18px", fontWeight: "500", color: "#111827", marginBottom: "4px" },
    subtitle: { fontSize: "13px", color: "#6b7280", marginBottom: "1.5rem" },
    label: { display: "block", fontSize: "12px", fontWeight: "500", color: "#6b7280", marginBottom: "5px", textTransform: "uppercase", letterSpacing: "0.04em" },
    inputWrap: { position: "relative", marginBottom: "1rem" },
    inputIcon: { position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "#9ca3af", pointerEvents: "none", fontSize: "16px" },
    input: { paddingLeft: "34px", width: "100%", height: "36px", border: "0.5px solid #d1d5db", borderRadius: "8px", fontSize: "14px", outline: "none", boxSizing: "border-box" },
    eyeBtn: { position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#9ca3af", fontSize: "16px", padding: "2px" },
    loginBtn: { width: "100%", padding: "9px", fontSize: "14px", fontWeight: "500", background: "#1B3A6B", color: "#fff", border: "none", borderRadius: "8px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" },
    errorBox: { background: "#fef2f2", border: "0.5px solid #fca5a5", borderRadius: "8px", padding: "9px 12px", fontSize: "13px", color: "#b91c1c", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "8px" },
    successBox: { background: "#f0fdf4", border: "0.5px solid #86efac", borderRadius: "8px", padding: "9px 12px", fontSize: "13px", color: "#15803d", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "8px" },
    hint: { marginTop: "1.25rem", paddingTop: "1rem", borderTop: "0.5px solid #f3f4f6", fontSize: "12px", color: "#9ca3af", textAlign: "center" },
    code: { fontFamily: "monospace", background: "#f3f4f6", padding: "1px 5px", borderRadius: "4px", fontSize: "11px", color: "#6b7280" },
  };

  function attempt() {
    setError("");
    if (!username.trim()) { setError("Please enter your username."); return; }
    if (!password)        { setError("Please enter your password."); return; }

    if (username === HARDCODED_USER.username && password === HARDCODED_USER.password) {
      sessionStorage.setItem("xrd_authed", "true");
      setSuccess(true);
      setTimeout(() => navigate("/dashboard"), 1200);
    } else {
      setError("Invalid username or password.");
      setPassword("");
    }
  }

  function onKey(e) { if (e.key === "Enter") attempt(); }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logoRow}>
          <div style={s.logoIcon}>
            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="#fff" strokeWidth="1.5">
              <circle cx="12" cy="12" r="3"/><path d="M12 2v2m0 16v2M4.22 4.22l1.42 1.42m12.72 12.72 1.42 1.42M2 12h2m16 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: "15px", fontWeight: "500", color: "#111827" }}>XRD Analysis</div>
            <div style={{ fontSize: "12px", color: "#9ca3af" }}>SSPL SIC Lab</div>
          </div>
        </div>

        <h2 style={s.heading}>Sign in</h2>
        <p style={s.subtitle}>Enter your credentials to access the system.</p>

        {error && (
          <div style={s.errorBox}>
            <span>⚠</span> {error}
          </div>
        )}
        {success && (
          <div style={s.successBox}>
            <span>✓</span> Login successful — redirecting…
          </div>
        )}

        <div>
          <label style={s.label} htmlFor="username">Username</label>
          <div style={s.inputWrap}>
            <span style={s.inputIcon}>👤</span>
            <input
              id="username"
              style={s.input}
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              onKeyDown={onKey}
              autoComplete="username"
            />
          </div>

          <label style={s.label} htmlFor="password">Password</label>
          <div style={{ ...s.inputWrap }}>
            <span style={s.inputIcon}>🔒</span>
            <input
              id="password"
              style={{ ...s.input, paddingRight: "38px" }}
              type={showPw ? "text" : "password"}
              placeholder="Enter password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={onKey}
              autoComplete="current-password"
            />
            <button style={s.eyeBtn} type="button" onClick={() => setShowPw(p => !p)} aria-label={showPw ? "Hide password" : "Show password"}>
              {showPw ? "🙈" : "👁"}
            </button>
          </div>

          <button style={s.loginBtn} type="button" onClick={attempt} disabled={success}>
            Sign in
          </button>
        </div>

        <div style={s.hint}>
          Demo credentials &nbsp;·&nbsp;
          <code style={s.code}>admin</code> / <code style={s.code}>xrd2024</code>
        </div>
      </div>
    </div>
  );
}