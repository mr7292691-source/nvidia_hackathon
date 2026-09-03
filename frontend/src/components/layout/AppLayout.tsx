import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/event", label: "Event Detail" },
  { to: "/approvals", label: "Approval Queue" },
  { to: "/replay-console", label: "Replay Console" },
];

export function AppLayout() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "system-ui, sans-serif" }}>
      <nav
        style={{
          width: 220,
          borderRight: "1px solid #ddd",
          padding: "1.5rem 1rem",
          background: "#0b1f33",
          color: "#fff",
        }}
      >
        <h1 style={{ fontSize: "1.1rem", marginBottom: "1.5rem" }}>LifeShield AI</h1>
        <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                style={({ isActive }) => ({
                  color: isActive ? "#7fd4ff" : "#fff",
                  textDecoration: "none",
                  fontWeight: isActive ? 600 : 400,
                })}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <main style={{ flex: 1, padding: "2rem" }}>
        <Outlet />
      </main>
    </div>
  );
}
