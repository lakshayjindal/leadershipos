import { useAppStore } from '../store';
import PlanningWorkspace from '../workspaces/PlanningWorkspace';
import WorkingWorkspace from '../workspaces/WorkingWorkspace';
import IdleWorkspace from '../workspaces/IdleWorkspace';
import ReviewWorkspace from '../workspaces/ReviewWorkspace';
import HistoryView from '../workspaces/HistoryView';
import SettingsView from '../workspaces/SettingsView';

export default function MainWorkspace() {
  const { currentState, workspaceView, todayStatus } = useAppStore();

  // If not on 'today' view, show dedicated views
  if (workspaceView === 'history') {
    return (
      <main className="main-workspace">
        <HistoryView />
      </main>
    );
  }

  if (workspaceView === 'settings') {
    return (
      <main className="main-workspace">
        <SettingsView onRefresh={() => {}} />
      </main>
    );
  }

  // State-driven workspace for 'today' view
  const renderContent = () => {
    switch (currentState) {
      case 'startup':
      case 'planning':
        return <PlanningWorkspace />;
      case 'working':
        return <WorkingWorkspace />;
      case 'idle':
        return <IdleWorkspace />;
      case 'review':
      case 'shutdown':
        return <ReviewWorkspace />;
      default:
        return <IdleWorkspace />;
    }
  };

  return (
    <main className={`main-workspace ${currentState === 'review' ? 'workspace-review' : ''}`}>
      {renderContent()}
    </main>
  );
}
