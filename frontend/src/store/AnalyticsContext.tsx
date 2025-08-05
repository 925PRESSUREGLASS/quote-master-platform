import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';
import { EventType } from '@/types';
import { apiService } from '@/services/api';

interface AnalyticsContextType {
  sessionId: string;
  trackEvent: (
    eventType: EventType | string,
    properties?: Record<string, any>
  ) => void;
  trackPageView: (url?: string, title?: string) => void;
  trackConversion: (goalName: string, value?: number) => void;
  isEnabled: boolean;
  setEnabled: (enabled: boolean) => void;
}

const AnalyticsContext = createContext<AnalyticsContextType | undefined>(
  undefined
);

interface AnalyticsProviderProps {
  children: ReactNode;
}

export function AnalyticsProvider({ children }: AnalyticsProviderProps) {
  const [sessionId] = useState(() => generateSessionId());
  const [isEnabled, setIsEnabled] = useState(true);
  const [eventQueue, setEventQueue] = useState<any[]>([]);

  // Initialize analytics
  useEffect(() => {
    // Check user preferences for analytics tracking
    const analyticsEnabled = localStorage.getItem('analytics_enabled');
    if (analyticsEnabled !== null) {
      setIsEnabled(JSON.parse(analyticsEnabled));
    }

    // Start session
    if (isEnabled) {
      startSession();
    }

    // Flush events periodically
    const flushInterval = setInterval(flushEvents, 5000);

    // Cleanup on unmount
    return () => {
      clearInterval(flushInterval);
      if (isEnabled) {
        endSession();
      }
      flushEvents();
    };
  }, []);

  // Update localStorage when enabled state changes
  useEffect(() => {
    localStorage.setItem('analytics_enabled', JSON.stringify(isEnabled));
  }, [isEnabled]);

  // Start user session
  const startSession = async () => {
    try {
      await apiService.post('/analytics/sessions', {
        session_id: sessionId,
        started_at: new Date().toISOString(),
        user_agent: navigator.userAgent,
        screen_resolution: `${screen.width}x${screen.height}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        referrer: document.referrer,
        landing_page: window.location.pathname,
      });
    } catch (error) {
      console.warn('Failed to start analytics session:', error);
    }
  };

  // End user session
  const endSession = async () => {
    try {
      await apiService.post('/analytics/sessions/end', {
        session_id: sessionId,
        ended_at: new Date().toISOString(),
      });
    } catch (error) {
      console.warn('Failed to end analytics session:', error);
    }
  };

  // Track an event
  const trackEvent = (
    eventType: EventType | string,
    properties: Record<string, any> = {}
  ) => {
    if (!isEnabled) return;

    const event = {
      event_type: eventType,
      event_name: properties.event_name || eventType,
      session_id: sessionId,
      properties: {
        ...properties,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        path: window.location.pathname,
        user_agent: navigator.userAgent,
      },
    };

    // Add to queue
    setEventQueue(prev => [...prev, event]);

    // Immediate flush for important events
    if (isImportantEvent(eventType)) {
      flushEvents();
    }
  };

  // Track page view
  const trackPageView = (url?: string, title?: string) => {
    if (!isEnabled) return;

    const pageUrl = url || window.location.href;
    const pageTitle = title || document.title;

    trackEvent(EventType.PAGE_VIEW, {
      event_name: 'page_view',
      page_url: pageUrl,
      page_title: pageTitle,
      page_path: new URL(pageUrl).pathname,
    });

    // Also send to dedicated page view endpoint
    queueApiCall('/analytics/page-views', {
      url: pageUrl,
      title: pageTitle,
      path: new URL(pageUrl).pathname,
      session_id: sessionId,
      viewed_at: new Date().toISOString(),
    });
  };

  // Track conversion
  const trackConversion = (goalName: string, value?: number) => {
    if (!isEnabled) return;

    trackEvent('conversion', {
      event_name: 'conversion',
      goal_name: goalName,
      value,
    });

    // Also send to dedicated conversion endpoint
    queueApiCall('/analytics/conversions', {
      goal_name: goalName,
      value,
      session_id: sessionId,
      converted_at: new Date().toISOString(),
    });
  };

  // Add API call to queue
  const queueApiCall = (endpoint: string, data: any) => {
    setEventQueue(prev => [
      ...prev,
      {
        type: 'api_call',
        endpoint,
        data,
      },
    ]);
  };

  // Flush events to server
  const flushEvents = async () => {
    if (eventQueue.length === 0 || !isEnabled) return;

    const eventsToSend = [...eventQueue];
    setEventQueue([]);

    try {
      // Separate regular events from API calls
      const regularEvents = eventsToSend.filter(e => e.type !== 'api_call');
      const apiCalls = eventsToSend.filter(e => e.type === 'api_call');

      // Send regular events
      if (regularEvents.length > 0) {
        await Promise.all(
          regularEvents.map(event =>
            apiService.post('/analytics/events', event).catch(error => {
              console.warn('Failed to send analytics event:', error);
              // Re-queue failed events
              setEventQueue(prev => [...prev, event]);
            })
          )
        );
      }

      // Send API calls
      if (apiCalls.length > 0) {
        await Promise.all(
          apiCalls.map(call =>
            apiService.post(call.endpoint, call.data).catch(error => {
              console.warn(`Failed to send analytics to ${call.endpoint}:`, error);
              // Re-queue failed calls
              setEventQueue(prev => [...prev, call]);
            })
          )
        );
      }
    } catch (error) {
      console.warn('Failed to flush analytics events:', error);
    }
  };

  // Check if event is important (should be sent immediately)
  const isImportantEvent = (eventType: string): boolean => {
    const importantEvents = [
      EventType.USER_REGISTER,
      EventType.USER_LOGIN,
      EventType.USER_LOGOUT,
      EventType.SUBSCRIPTION_UPGRADED,
    ];
    return importantEvents.includes(eventType as EventType);
  };

  const value = {
    sessionId,
    trackEvent,
    trackPageView,
    trackConversion,
    isEnabled,
    setEnabled: setIsEnabled,
  };

  return (
    <AnalyticsContext.Provider value={value}>
      {children}
    </AnalyticsContext.Provider>
  );
}

export function useAnalytics() {
  const context = useContext(AnalyticsContext);
  if (context === undefined) {
    throw new Error('useAnalytics must be used within an AnalyticsProvider');
  }
  return context;
}

// Utility function to generate session ID
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export { AnalyticsContext };