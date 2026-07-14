import { emit } from '@tauri-apps/api/event';
import { formatDurationShort } from './utils';

async function getOverlayWindow() {
  try {
    const { WebviewWindow } = await import('@tauri-apps/api/webviewWindow');
    return await WebviewWindow.getByLabel('overlay');
  } catch {
    return null;
  }
}

export async function showOverlay() {
  try {
    const win = await getOverlayWindow();
    if (win) {
      await win.show();
      await win.setFocus();
    }
  } catch (e) {
    console.error('Failed to show overlay:', e);
  }
}

export async function hideOverlay() {
  try {
    const win = await getOverlayWindow();
    if (win) {
      await win.hide();
    }
  } catch (e) {
    console.error('Failed to hide overlay:', e);
  }
}

export async function updateOverlay(
  taskTitle: string | null,
  elapsedSeconds: number,
  status: string,
  nextTaskTitle?: string
) {
  try {
    await emit('overlay-update', {
      task: taskTitle || 'No active task',
      timer: formatDurationShort(elapsedSeconds),
      status: status || 'idle',
      next: nextTaskTitle || '—',
    });
  } catch (e) {
    console.error('Failed to update overlay:', e);
  }
}
