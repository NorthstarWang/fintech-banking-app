
interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

interface PerformanceReport {
  metrics: PerformanceMetric[];
  summary: {
    averageLoadTime: number;
    p95LoadTime: number;
    totalRequests: number;
    errorRate: number;
    cacheHitRate: number;
  };
}

export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: PerformanceMetric[] = [];
  private observers: Map<string, PerformanceObserver> = new Map();
  private resourceTimings: Map<string, number> = new Map();
  private cacheHits = 0;
  private cacheMisses = 0;
  private errors = 0;
  private requests = 0;

  private constructor() {
    if (typeof window !== 'undefined') {
      this.initializeObservers();
    }
  }

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  /**
   * Initialize performance observers
   */
  private initializeObservers(): void {
    // Observe navigation timing
    if ('PerformanceObserver' in window) {
      // Navigation timing
      try {
        const navigationObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'navigation') {
              const navEntry = entry as PerformanceNavigationTiming;
              this.recordMetric('page-load', navEntry.loadEventEnd - navEntry.fetchStart, {
                redirectTime: navEntry.redirectEnd - navEntry.redirectStart,
                dnsTime: navEntry.domainLookupEnd - navEntry.domainLookupStart,
                connectTime: navEntry.connectEnd - navEntry.connectStart,
                requestTime: navEntry.responseStart - navEntry.requestStart,
                responseTime: navEntry.responseEnd - navEntry.responseStart,
                domProcessing: navEntry.domComplete - navEntry.domInteractive,
                loadComplete: navEntry.loadEventEnd - navEntry.loadEventStart,
              });
            }
          }
        });
        navigationObserver.observe({ entryTypes: ['navigation'] });
        this.observers.set('navigation', navigationObserver);
      } catch {
      }

      // Resource timing
      try {
        const resourceObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'resource') {
              const resourceEntry = entry as PerformanceResourceTiming;
              this.resourceTimings.set(entry.name, resourceEntry.duration);
              
              // Track cache hits
              if (resourceEntry.transferSize === 0 && resourceEntry.decodedBodySize > 0) {
                this.cacheHits++;
              } else {
                this.cacheMisses++;
              }
            }
          }
        });
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.set('resource', resourceObserver);
      } catch {
      }

      // Largest Contentful Paint
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          this.recordMetric('lcp', lastEntry.startTime);
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.set('lcp', lcpObserver);
      } catch {
      }

      // First Input Delay
      try {
        const fidObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'first-input') {
              const fidEntry = entry as PerformanceEventTiming;
              this.recordMetric('fid', fidEntry.processingStart - fidEntry.startTime);
            }
          }
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.set('fid', fidObserver);
      } catch {
      }

      // Cumulative Layout Shift
      try {
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const layoutShiftEntry = entry as PerformanceEntry & { hadRecentInput?: boolean; value?: number };
            if (entry.entryType === 'layout-shift' && !layoutShiftEntry.hadRecentInput) {
              clsValue += layoutShiftEntry.value || 0;
              this.recordMetric('cls', clsValue);
            }
          }
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.set('cls', clsObserver);
      } catch {
      }
    }
  }

  /**
   * Record a performance metric
   */
  recordMetric(name: string, value: number, metadata?: Record<string, unknown>): void {
    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      metadata
    };

    this.metrics.push(metric);

    // Keep only last 1000 metrics to prevent memory issues
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-500);
    }

  }

  /**
   * Mark the start of a performance measurement
   */
  mark(name: string): void {
    if ('performance' in window && 'mark' in window.performance) {
      performance.mark(name);
    }
  }

  /**
   * Measure between two marks
   */
  measure(name: string, startMark: string, endMark?: string): number {
    if ('performance' in window && 'measure' in window.performance) {
      try {
        if (endMark) {
          performance.measure(name, startMark, endMark);
        } else {
          performance.measure(name, startMark);
        }
        
        const measures = performance.getEntriesByName(name, 'measure');
        if (measures.length > 0) {
          const duration = measures[measures.length - 1].duration;
          this.recordMetric(name, duration);
          return duration;
        }
      } catch {
      }
    }
    return 0;
  }

  /**
   * Track API request performance
   */
  trackAPIRequest(url: string, duration: number, success: boolean): void {
    this.requests++;
    if (!success) this.errors++;
    
    this.recordMetric('api-request', duration, {
      url,
      success,
      cached: duration < 50 // Assume very fast responses are cached
    });
  }

  /**
   * Track component render time
   */
  trackComponentRender(componentName: string, duration: number): void {
    this.recordMetric('component-render', duration, {
      component: componentName
    });
  }

  /**
   * Get performance report
   */
  getReport(): PerformanceReport {
    const loadTimes = this.metrics
      .filter(m => m.name === 'page-load')
      .map(m => m.value)
      .sort((a, b) => a - b);

    const averageLoadTime = loadTimes.length > 0
      ? loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length
      : 0;

    const p95Index = Math.floor(loadTimes.length * 0.95);
    const p95LoadTime = loadTimes[p95Index] || 0;

    const cacheTotal = this.cacheHits + this.cacheMisses;
    const cacheHitRate = cacheTotal > 0 ? this.cacheHits / cacheTotal : 0;

    const errorRate = this.requests > 0 ? this.errors / this.requests : 0;

    return {
      metrics: this.metrics,
      summary: {
        averageLoadTime,
        p95LoadTime,
        totalRequests: this.requests,
        errorRate,
        cacheHitRate
      }
    };
  }

  /**
   * Get Core Web Vitals
   */
  getCoreWebVitals(): {
    lcp?: number;
    fid?: number;
    cls?: number;
    ttfb?: number;
  } {
    const lcp = this.metrics
      .filter(m => m.name === 'lcp')
      .sort((a, b) => b.timestamp - a.timestamp)[0]?.value;

    const fid = this.metrics
      .filter(m => m.name === 'fid')
      .sort((a, b) => b.timestamp - a.timestamp)[0]?.value;

    const cls = this.metrics
      .filter(m => m.name === 'cls')
      .sort((a, b) => b.timestamp - a.timestamp)[0]?.value;

    // Calculate TTFB
    let ttfb: number | undefined;
    if ('performance' in window && 'timing' in window.performance) {
      const timing = window.performance.timing;
      ttfb = timing.responseStart - timing.navigationStart;
    }

    return { lcp, fid, cls, ttfb };
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics = [];
    this.resourceTimings.clear();
    this.cacheHits = 0;
    this.cacheMisses = 0;
    this.errors = 0;
    this.requests = 0;
  }

  /**
   * Destroy observers
   */
  destroy(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
    this.clear();
  }
}

// Export singleton instance
export const performanceMonitor = PerformanceMonitor.getInstance();

// React hook for performance monitoring
import { useRef, useEffect } from 'react';

export function usePerformanceMonitor() {
  const monitor = useRef(performanceMonitor);

  useEffect(() => {
    return () => {
      // Don't destroy the singleton on unmount
    };
  }, []);

  return {
    mark: (name: string) => monitor.current.mark(name),
    measure: (name: string, startMark: string, endMark?: string) => 
      monitor.current.measure(name, startMark, endMark),
    trackAPIRequest: (url: string, duration: number, success: boolean) =>
      monitor.current.trackAPIRequest(url, duration, success),
    trackComponentRender: (componentName: string, duration: number) =>
      monitor.current.trackComponentRender(componentName, duration),
    getReport: () => monitor.current.getReport(),
    getCoreWebVitals: () => monitor.current.getCoreWebVitals()
  };
}
