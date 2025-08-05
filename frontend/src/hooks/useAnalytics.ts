import { useLocation } from 'react-router-dom';
import { useEffect, useRef } from 'react';
import { useAnalytics as useAnalyticsContext } from '@/store/AnalyticsContext';

export function useAnalytics() {
  const location = useLocation();
  const { trackPageView: trackPageViewContext, ...analyticsContext } = useAnalyticsContext();
  const previousLocation = useRef<string>();

  // Auto-track page views on route changes
  useEffect(() => {
    const currentPath = location.pathname + location.search;
    
    // Only track if location actually changed
    if (previousLocation.current !== currentPath) {
      trackPageViewContext(window.location.href, document.title);
      previousLocation.current = currentPath;
    }
  }, [location, trackPageViewContext]);

  // Return enhanced trackPageView that can be called manually
  const trackPageView = (url?: string, title?: string) => {
    trackPageViewContext(url, title);
  };

  return {
    ...analyticsContext,
    trackPageView,
  };
}