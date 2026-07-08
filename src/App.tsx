import { SessionProvider, useSession } from "./contexts/SessionContext";
import { MainLayout } from "./layouts/MainLayout";
import { Loading } from "./pages/Loading";
import { Welcome } from "./pages/Welcome";
import { Planning } from "./pages/Planning";
import { Commitment } from "./pages/Commitment";
import { Dashboard } from "./pages/Dashboard";
import { ReflectionPage } from "./pages/Reflection";
import { SettingsPage } from "./pages/SettingsPage";

function AppContent() {
  const { view } = useSession();

  const renderPage = () => {
    switch (view) {
      case "loading":
        return <Loading />;
      case "welcome":
        return <Welcome />;
      case "planning":
        return <Planning />;
      case "commitment":
        return <Commitment />;
      case "dashboard":
        return <Dashboard />;
      case "reflection":
        return <ReflectionPage />;
      case "settings":
        return <SettingsPage />;
      default:
        return <Welcome />;
    }
  };

  return <MainLayout>{renderPage()}</MainLayout>;
}

function App() {
  return (
    <SessionProvider>
      <AppContent />
    </SessionProvider>
  );
}

export default App;
