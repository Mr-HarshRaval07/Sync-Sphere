import { useEffect, useRef, useState } from 'react';
import { useOrgStore } from '../../../shared/stores/orgStore';
import { useOperationsStore, ActivityEvent } from '../stores/operationsStore';
import { toast } from 'sonner';

export const useOperationsTelemetry = () => {
  const currentOrg = useOrgStore((state) => state.currentOrg);
  const { setTelemetryData, addActivityEvent, alerts, setAlerts } = useOperationsStore();
  const [isConnected, setIsConnected] = useState(false);
  
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  useEffect(() => {
    if (!currentOrg) return;

    const connect = () => {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = process.env.NEXT_PUBLIC_WS_URL || 'localhost:8000';
      const wsUrl = `${wsProtocol}//${wsHost}/v1/observability/live?org_id=${currentOrg.id}`;

      console.log(`[WebSocket Operations] Connecting to ${wsUrl}`);
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('[WebSocket Operations] Live stream connected.');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }

        // Add visual connected milestone to feed
        addActivityEvent({
          id: 'ws-conn-' + Date.now(),
          timestamp: new Date().toISOString(),
          type: 'execution_completed',
          message: 'Real-time telemetry link established with API gateway.',
        });
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const { type, payload } = message;

          if (type === 'metric') {
            // Process metrics directly into store
            setTelemetryData(payload);

            // Dynamically evaluate SLAs based on incoming metrics
            if (payload.avgLatencyMs !== undefined) {
              useOperationsStore.getState().updateSlaTarget('latency', payload.avgLatencyMs);
            }
            if (payload.successRate !== undefined) {
              useOperationsStore.getState().updateSlaTarget('successRate', payload.successRate);
            }
            if (payload.errorRate !== undefined) {
              useOperationsStore.getState().updateSlaTarget('errorRate', payload.errorRate);
            }
            if (payload.workerUtilization !== undefined) {
              useOperationsStore.getState().updateSlaTarget('workerUtilization', payload.workerUtilization);
            }
          } else if (type === 'trace') {
            // Log execution updates to activity feed
            const eventTypeMap: Record<string, ActivityEvent['type']> = {
              running: 'execution_started',
              completed: 'execution_completed',
              failed: 'execution_failed',
            };

            const isEndStep = payload.node_id === 'end' || payload.node_id === 'end_1';
            let eventType: ActivityEvent['type'] = 'execution_started';
            if (payload.status === 'failed') eventType = 'execution_failed';
            else if (payload.status === 'success' && isEndStep) eventType = 'execution_completed';

            addActivityEvent({
              id: payload.span_id || 'trace-' + Date.now(),
              timestamp: payload.completed_at || payload.started_at || new Date().toISOString(),
              type: eventType,
              message: `Execution #${payload.session_id.slice(-6)} step "${payload.node_id}" status: ${payload.status}`,
              meta: payload,
            });
          } else if (type === 'alert') {
            // Append alert and trigger notification
            const newAlert = {
              id: payload.alert_id || 'alert-' + Date.now(),
              org_id: currentOrg.id,
              name: payload.name || 'System Alert',
              message: payload.message || 'Operational threshold breached.',
              severity: payload.severity || 'WARNING',
              status: 'ACTIVE' as const,
              created_at: new Date().toISOString(),
            };

            setAlerts([newAlert, ...alerts]);

            addActivityEvent({
              id: newAlert.id,
              timestamp: newAlert.created_at,
              type: 'alert_triggered',
              message: `[${newAlert.severity}] ${newAlert.name}: ${newAlert.message}`,
            });

            toast.warning(newAlert.name, {
              description: newAlert.message,
              duration: 5000,
            });
          }
        } catch (err) {
          console.error('[WebSocket Operations] Parse error:', err);
        }
      };

      socket.onerror = (error) => {
        console.error('[WebSocket Operations] Connection error:', error);
      };

      socket.onclose = (event) => {
        setIsConnected(false);
        console.log('[WebSocket Operations] Link closed:', event.reason);
        
        // Attempt reconnection with exponential backoff capped at 30s
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current += 1;
        
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
  }, [currentOrg, setTelemetryData, addActivityEvent, alerts, setAlerts]);

  return { isConnected };
};
export default useOperationsTelemetry;
