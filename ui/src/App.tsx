import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { Chrome } from "./components/Chrome";
import { MarketingShell } from "./components/MarketingShell";
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
import SiteDemo from "./pages/site/SiteDemo";
import SiteHome from "./pages/site/SiteHome";
import SiteHowItWorks from "./pages/site/SiteHowItWorks";
import SitePricing from "./pages/site/SitePricing";
import SiteTryXyntra from "./pages/site/SiteTryXyntra";
import { APP_PREFIX } from "./lib/routes";

function ConsoleShell() {
  return (
    <Chrome>
      <Outlet />
    </Chrome>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<MarketingShell />}>
        <Route path="/" element={<SiteHome />} />
        <Route path="/try-xyntra" element={<SiteTryXyntra />} />
        <Route path="/pricing" element={<SitePricing />} />
        <Route path="/how-it-works" element={<SiteHowItWorks />} />
        <Route path="/demo" element={<SiteDemo />} />
        <Route path="/site" element={<Navigate replace to="/" />} />
        <Route
          path="/site/try-xyntra"
          element={<Navigate replace to="/try-xyntra" />}
        />
        <Route path="/site/pricing" element={<Navigate replace to="/pricing" />} />
        <Route
          path="/site/how-it-works"
          element={<Navigate replace to="/how-it-works" />}
        />
        <Route path="/site/demo" element={<Navigate replace to="/demo" />} />
      </Route>
      <Route element={<ConsoleShell />}>
        <Route path={APP_PREFIX} element={<Dashboard />} />
        <Route path={`${APP_PREFIX}/chat`} element={<Chat />} />
        <Route path={`${APP_PREFIX}/projects`} element={<Projects />} />
        <Route path={`${APP_PREFIX}/sessions`} element={<Sessions />} />
        <Route path={`${APP_PREFIX}/tasks`} element={<Tasks />} />
        <Route path={`${APP_PREFIX}/leaderboard`} element={<Leaderboard />} />
        <Route path={`${APP_PREFIX}/compare`} element={<Compare />} />
        <Route
          path={`${APP_PREFIX}/provider-health`}
          element={<ProviderHealth />}
        />
        <Route
          path={`${APP_PREFIX}/routing-decision`}
          element={<RoutingDecision />}
        />
        <Route path={`${APP_PREFIX}/memory`} element={<Memory />} />
        <Route
          path={`${APP_PREFIX}/context-inspector`}
          element={<ContextInspector />}
        />
        <Route
          path={`${APP_PREFIX}/semantic-cache`}
          element={<SemanticCache />}
        />
        <Route path={`${APP_PREFIX}/artifacts`} element={<Artifacts />} />
        <Route
          path={`${APP_PREFIX}/prompt-templates`}
          element={<PromptTemplates />}
        />
        <Route
          path={`${APP_PREFIX}/spend-analytics`}
          element={<SpendAnalytics />}
        />
        <Route path={`${APP_PREFIX}/replay`} element={<Replay />} />
        <Route path={`${APP_PREFIX}/event-log`} element={<EventLog />} />
        <Route path={`${APP_PREFIX}/policies`} element={<Policies />} />
        <Route path={`${APP_PREFIX}/approvals`} element={<Approvals />} />
        <Route path={`${APP_PREFIX}/api-keys`} element={<ApiKeys />} />
        <Route path={`${APP_PREFIX}/webhooks`} element={<Webhooks />} />
        <Route path={`${APP_PREFIX}/evals`} element={<Evals />} />
        <Route path={`${APP_PREFIX}/settings`} element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  );
}
