type EventCallback = (...args: unknown[]) => void;

class EventBus {
  private events: Map<string, EventCallback[]> = new Map();

  on(event: string, callback: EventCallback): () => void {
    if (!this.events.has(event)) {
      this.events.set(event, []);
    }
    this.events.get(event)!.push(callback);

    // Return unsubscribe function
    return () => this.off(event, callback);
  }

  off(event: string, callback: EventCallback): void {
    const callbacks = this.events.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event: string, ...args: unknown[]): void {
    const callbacks = this.events.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(...args);
        } catch {
        }
      });
    }
  }

  clear(): void {
    this.events.clear();
  }
}

// Create a singleton instance
export const eventBus = new EventBus();

// Event names
export const EVENTS = {
  BALANCE_UPDATE: 'balance:update',
  ACCOUNT_UPDATE: 'account:update',
  TRANSACTION_CREATED: 'transaction:created',
  TRANSFER_COMPLETED: 'transfer:completed',
  NOTIFICATION_RECEIVED: 'notification:received',
} as const;