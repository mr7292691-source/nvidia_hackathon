import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { EventDetail } from "./pages/EventDetail";
import { ApprovalQueue } from "./pages/ApprovalQueue";
import { ReplayConsole } from "./pages/ReplayConsole";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="event" element={<EventDetail />} />
          <Route path="approvals" element={<ApprovalQueue />} />
          <Route path="replay-console" element={<ReplayConsole />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
