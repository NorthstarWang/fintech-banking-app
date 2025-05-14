import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

interface PortalProps {
  children: React.ReactNode;
  containerId?: string;
}

export const Portal: React.FC<PortalProps> = ({ 
  children, 
  containerId = 'portal-root' 
}) => {
  const [mounted, setMounted] = useState(false);
  const portalRootRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    // Find or create portal container
    let portalRoot = document.getElementById(containerId);
    
    if (!portalRoot) {
      portalRoot = document.createElement('div');
      portalRoot.id = containerId;
      // Remove fixed positioning and pointer-events from container
      // Let children handle their own positioning
      document.body.appendChild(portalRoot);
    }
    
    portalRootRef.current = portalRoot;
    setMounted(true);

    // Don't remove the portal root on cleanup - let it persist
    // This prevents errors when multiple components use the same portal
    return () => {
      // Reset the ref but don't remove the DOM element
      portalRootRef.current = null;
    };
  }, [containerId]);

  if (!mounted || !portalRootRef.current) {
    return null;
  }

  return createPortal(
    children,
    portalRootRef.current
  );
};

export default Portal;