import { useRef, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface HoverTrackingOptions {
  elementId: string;
  elementName: string;
  minHoverDuration?: number; // Minimum hover duration in ms before logging
  trackDuration?: boolean; // Whether to track hover duration
}

export const useHoverTracking = ({
  elementId,
  elementName,
  minHoverDuration = 500,
  trackDuration = true
}: HoverTrackingOptions) => {
  const { user } = useAuth();
  const hoverStartTimeRef = useRef<number>(0);
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const hasLoggedRef = useRef(false);

  const handleMouseEnter = useCallback((event?: React.MouseEvent) => {
    hoverStartTimeRef.current = Date.now();
    hasLoggedRef.current = false;

    // Capture element type before setTimeout (event object gets recycled)
    const elementType = event?.currentTarget?.tagName?.toLowerCase() || 'unknown';

    // Log hover after minimum duration
    hoverTimeoutRef.current = setTimeout(() => {
      if (!hasLoggedRef.current) {
          text: `User ${user?.username || 'unknown'} hovered over ${elementName}`,
          element_identifier: elementId,
          data: {
            user_id: user?.id,
            hover_start: new Date(hoverStartTimeRef.current).toISOString(),
            element_type: elementType,
            timestamp: new Date().toISOString()
          }
        });
        hasLoggedRef.current = true;
      }
    }, minHoverDuration);
  }, [elementId, elementName, user, minHoverDuration]);

  const handleMouseLeave = useCallback(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    if (trackDuration && hasLoggedRef.current && hoverStartTimeRef.current > 0) {
      const hoverDuration = Date.now() - hoverStartTimeRef.current;
      
        text: `User ${user?.username || 'unknown'} finished hovering over ${elementName} after ${(hoverDuration / 1000).toFixed(1)}s`,
        element_identifier: `${elementId}-end`,
        data: {
          user_id: user?.id,
          hover_duration_ms: hoverDuration,
          hover_duration_seconds: parseFloat((hoverDuration / 1000).toFixed(1)),
          timestamp: new Date().toISOString()
        }
      });
    }

    hoverStartTimeRef.current = 0;
  }, [elementId, elementName, user, trackDuration]);

  // Return props to spread on the element
  return {
    onMouseEnter: handleMouseEnter,
    onMouseLeave: handleMouseLeave,
    'data-hover-tracked': 'true'
  };
};
