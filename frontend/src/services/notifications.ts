export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: string;
  read: boolean;
}

class NotificationsService {
  private notifications: Notification[] = [
    {
      id: '1',
      title: 'Welcome to Banking App',
      message: 'Your account has been successfully created.',
      type: 'success',
      timestamp: new Date().toISOString(),
      read: false
    },
    {
      id: '2',
      title: 'Security Alert',
      message: 'New login detected from Chrome on Windows',
      type: 'info',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      read: false
    }
  ];

  async getNotifications(): Promise<Notification[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 100));
    return this.notifications;
  }

  async markAsRead(id: string): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 100));
    const notification = this.notifications.find(n => n.id === id);
    if (notification) {
      notification.read = true;
    }
  }

  async markAllAsRead(): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 100));
    this.notifications.forEach(n => n.read = true);
  }

  getUnreadCount(): number {
    return this.notifications.filter(n => !n.read).length;
  }
}

export const notificationsService = new NotificationsService();