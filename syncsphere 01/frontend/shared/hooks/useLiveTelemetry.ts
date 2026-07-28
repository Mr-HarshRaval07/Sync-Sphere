import { useEffect, useRef, useState } from 'react';
import { useOrgStore } from '../stores/orgStore';
import { useNotificationStore } from '../stores/notificationStore';
import { toast } from 'sonner';

export const useLiveTelemetry = () => {
  const currentOrg = useOrgStore((state) => state.currentOrg);
  const addNotification = useNotificationStore((state) => state.addNotification);
  const [isConnected, setIsConnected] = useState(false);
  const [latestMetric, setLatestMetric] = useState<any>(null);
  const [latestTrace, setLatestTrace] = useState<any>(null);
  
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  useEffect(() => {
    if (!currentOrg) return;

    const connect = () => {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = process.env.NEXT_PUBLIC_WS_URL || 'localhost:8000';
      const wsUrl = `${wsProtocol}//${wsHost}/v1/observability/live?org_id=${currentOrg.id}`;

      console.log(`[WebSocket] Connecting to ${wsUrl}`);
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('[WebSocket] Live telemetry stream connected.');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const { type, payload } = message;

          if (type === 'metric') {
            setLatestMetric(payload);
          } else if (type === 'trace') {
            setLatestTrace(payload);
          } else if (type === 'alert') {
            // Add to notification store and trigger UI toast
            addNotification({
              id: payload.alert_id || 'alert-' + Date.now(),
              org_id: currentOrg.id,
              name: payload.name || 'System Alert',
              message: payload.message || 'An alert was raised.',
              severity: payload.severity || 'WARNING',
              status: 'ACTIVE',
            });
            toast(payload.name || 'System Alert', {
              description: payload.message,
              action: {
                label: 'View',
                onClick: () => {
                  if (typeof window !== 'undefined') {
                    window.location.href = '/dashboard/observability';
                  }
                },
              },
            });
          }
        } catch (err) {
          console.error('[WebSocket] Error parsing message:', err);
        }
      };

      socket.onerror = (error) => {
        // Backend websocket may not be implemented in dev; avoid noisy console errors.
        console.debug('[WebSocket] Connection error (non-fatal):', error);
      };


      socket.onclose = (event) => {
        setIsConnected(false);
        console.log('[WebSocket] Connection closed:', event.reason);
        
        // Attempt reconnection with exponential backoff capped at 30s
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current += 1;
        
        console.log(`[WebSocket] Attempting reconnection in ${delay}ms...`);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    };

    connect();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [currentOrg, addNotification]);

  return { isConnected, latestMetric, latestTrace };
};
export default useLiveTelemetry;
