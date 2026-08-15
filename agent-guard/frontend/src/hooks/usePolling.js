import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for polling an async function at regular intervals.
 * Automatically stops polling when shouldPoll returns false.
 *
 * @param {Function} fetchFn - Async function to call on each poll
 * @param {number} interval - Polling interval in milliseconds
 * @param {boolean} enabled - Whether polling is active
 * @returns {{ data: any, loading: boolean, error: any }}
 */
export function usePolling(fetchFn, interval = 2000, enabled = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);
  const fetchRef = useRef(fetchFn);

  // Keep fetchFn ref up to date without triggering re-renders
  useEffect(() => {
    fetchRef.current = fetchFn;
  }, [fetchFn]);

  const poll = useCallback(async () => {
    try {
      const result = await fetchRef.current();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    // Initial fetch
    poll();

    // Set up interval
    timerRef.current = setInterval(poll, interval);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [poll, interval, enabled]);

  return { data, loading, error };
}
