import { useCallback, useEffect, useRef } from 'react';

type AbortControllerApi = {
  abort: () => void;
  reset: () => AbortSignal;
};

export default function useAbortController(): AbortControllerApi {
  const controllerRef = useRef<AbortController>(new AbortController());

  const abort = useCallback(() => {
    if (!controllerRef.current.signal.aborted) {
      controllerRef.current.abort();
    }
  }, []);

  const reset = useCallback(() => {
    controllerRef.current = new AbortController();
    return controllerRef.current.signal;
  }, []);

  useEffect(() => {
    return () => {
      if (!controllerRef.current.signal.aborted) {
        controllerRef.current.abort();
      }
    };
  }, []);

  return {
    // Call reset() for a fresh, non-stale signal before each request.
    abort,
    reset,
  };
}