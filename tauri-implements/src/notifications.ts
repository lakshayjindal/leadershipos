import { isPermissionGranted, requestPermission, sendNotification } from '@tauri-apps/plugin-notification';

let permissionGranted: boolean | null = null;

async function ensurePermission(): Promise<boolean> {
  if (permissionGranted !== null) return permissionGranted;
  try {
    permissionGranted = await isPermissionGranted();
    if (!permissionGranted) {
      const permission = await requestPermission();
      permissionGranted = permission === 'granted';
    }
  } catch (e) {
    console.error('Notification permission error:', e);
    permissionGranted = false;
  }
  return permissionGranted;
}

export async function notifyTimerStarted(taskTitle: string) {
  const ok = await ensurePermission();
  if (!ok) return;
  try {
    sendNotification({
      title: 'Focus Session Started',
      body: `Now working on: ${taskTitle}`,
    });
  } catch (e) {
    console.error('Failed to send notification:', e);
  }
}

export async function notifyTimerPaused(taskTitle: string, elapsedFormatted: string) {
  const ok = await ensurePermission();
  if (!ok) return;
  try {
    sendNotification({
      title: 'Focus Session Paused',
      body: `Paused "${taskTitle}" after ${elapsedFormatted}`,
    });
  } catch (e) {
    console.error('Failed to send notification:', e);
  }
}

export async function notifyTimerCompleted(taskTitle: string, elapsedFormatted: string) {
  const ok = await ensurePermission();
  if (!ok) return;
  try {
    sendNotification({
      title: '✅ Task Completed!',
      body: `Finished "${taskTitle}" — Total: ${elapsedFormatted}`,
    });
  } catch (e) {
    console.error('Failed to send notification:', e);
  }
}
