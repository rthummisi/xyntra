import { Navigate, Route, Routes } from "react-router-dom";
import { Chrome } from "./components/Chrome";
import ApiKeys from "./pages/ApiKeys";
import Approvals from "./pages/Approvals";
import Artifacts from "./pages/Artifacts";
import Chat from "./pages/Chat";
import Compare from "./pages/Compare";
import ContextInspector from "./pages/ContextInspector";
import Dashboard from "./pages/Dashboard";
import EventLog from "./pages/EventLog";
import Evals from "./pages/Evals";
import Leaderboard from "./pages/Leaderboard";
import Memory from "./pages/Memory";
import Policies from "./pages/Policies";
import Projects from "./pages/Projects";
import PromptTemplates from "./pages/PromptTemplates";
import ProviderHealth from "./pages/ProviderHealth";
import Replay from "./pages/Replay";
import RoutingDecision from "./pages/RoutingDecision";
import SemanticCache from "./pages/SemanticCache";
import Sessions from "./pages/Sessions";
import Settings from "./pages/Settings";
import SpendAnalytics from "./pages/SpendAnalytics";
import Tasks from "./pages/Tasks";
import Webhooks from "./pages/Webhooks";

export default function App() {
  return (
    <Chrome>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/sessions" element={<Sessions />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/provider-health" element={<ProviderHealth />} />
        <Route path="/routing-decision" element={<RoutingDecision />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/context-inspector" element={<ContextInspector />} />
        <Route path="/semantic-cache" element={<SemanticCache />} />
        <Route path="/artifacts" element={<Artifacts />} />
        <Route path="/prompt-templates" element={<PromptTemplates />} />
        <Route path="/spend-analytics" element={<SpendAnalytics />} />
        <Route path="/replay" element={<Replay />} />
        <Route path="/event-log" element={<EventLog />} />
        <Route path="/policies" element={<Policies />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/api-keys" element={<ApiKeys />} />
        <Route path="/webhooks" element={<Webhooks />} />
        <Route path="/evals" element={<Evals />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate replace to="/" />} />
      </Routes>
    </Chrome>
  );
}
