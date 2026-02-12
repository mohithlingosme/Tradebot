import { io, Socket } from 'socket.io-client';

export interface RealtimeEvent {
  event_id: string;
  type: string;
  ts: number;
  entity_id: string;
  payload: any;
  version: number;
}

export type EventHandler = (event: RealtimeEvent) => void;

export class RealtimeClient {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private eventHandlers: Map<string, EventHandler[]> = new Map();
  private processedEventIds = new Set<string>();
  private connectionStatus: 'disconnected' | 'connecting' | 'connected' = 'disconnected';
  private lastEventTimestamp = 0;

  constructor(private baseUrl: string = process.env.REACT_APP_API_URL || 'http://localhost:8000') {}

  connect(token: string): void {
    if (this.socket?.connected) return;

    this.connectionStatus = 'connecting';

    this.socket = io(`${this.baseUrl}/realtime`, {
      auth: { token },
      transports: ['websocket', 'polling'],
      timeout: 5000,
    });

    this.socket.on('connect', () => {
      console.log('[Realtime] Connected');
      this.connectionStatus = 'connected';
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
    });

    this.socket.on('disconnect', (reason: string) => {
      console.log('[Realtime] Disconnected:', reason);
      this.connectionStatus = 'disconnected';

      if (reason === 'io server disconnect' || reason === 'io client disconnect') {
        // Server/client initiated disconnect, don't auto-reconnect
        return;
      }

      this.attemptReconnect(token);
    });

    this.socket.on('connect_error', (error: Error) => {
      console.error('[Realtime] Connection error:', error);
      this.connectionStatus = 'disconnected';
      this.attemptReconnect(token);
    });

    this.socket.on('event', (event: RealtimeEvent) => {
      this.handleEvent(event);
    });

    this.socket.on('heartbeat', () => {
      // Respond to heartbeat
      this.socket?.emit('heartbeat_ack');
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.connectionStatus = 'disconnected';
    this.processedEventIds.clear();
  }

  private attemptReconnect(token: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[Realtime] Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`[Realtime] Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectDelay}ms`);

    setTimeout(() => {
      this.connect(token);
    }, this.reconnectDelay);

    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Exponential backoff, max 30s
  }

  private handleEvent(event: RealtimeEvent): void {
    // Deduplication
    if (this.processedEventIds.has(event.event_id)) {
      console.log('[Realtime] Duplicate event ignored:', event.event_id);
      return;
    }

    this.processedEventIds.add(event.event_id);
    this.lastEventTimestamp = Date.now();

    // Keep only recent event IDs to prevent memory leak
    if (this.processedEventIds.size > 1000) {
      const oldest = this.processedEventIds.values().next().value;
      if (oldest) {
        this.processedEventIds.delete(oldest);
      }
    }

    // Notify handlers
    const handlers = this.eventHandlers.get(event.type) || [];
    handlers.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error('[Realtime] Error in event handler:', error);
      }
    });
  }

  on(eventType: string, handler: EventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType)!.push(handler);
  }

  off(eventType: string, handler?: EventHandler): void {
    if (!handler) {
      this.eventHandlers.delete(eventType);
      return;
    }

    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  getConnectionStatus(): 'disconnected' | 'connecting' | 'connected' {
    return this.connectionStatus;
  }

  getLastEventTimestamp(): number {
    return this.lastEventTimestamp;
  }

  isConnected(): boolean {
    return this.connectionStatus === 'connected';
  }
}

// Singleton instance
export const realtimeClient = new RealtimeClient();
