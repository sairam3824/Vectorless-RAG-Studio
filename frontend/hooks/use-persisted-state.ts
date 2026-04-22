"use client";

import { Dispatch, SetStateAction, useEffect, useState } from "react";


export function usePersistedState<T>(key: string, initialValue: T): [T, Dispatch<SetStateAction<T>>, boolean] {
  const [state, setState] = useState<T>(initialValue);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(key);
      if (raw !== null) {
        setState(JSON.parse(raw) as T);
      }
    } catch {
      // Ignore malformed browser state and fall back to the initial value.
    } finally {
      setHydrated(true);
    }
  }, [key]);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(key, JSON.stringify(state));
  }, [hydrated, key, state]);

  return [state, setState, hydrated];
}
