import { useState } from 'react';

export interface InputHistory {
  add: (entry: string) => void;
  navigateUp: () => string;
  navigateDown: () => string;
}

export const useInputHistory = (): InputHistory => {
  const [history, setHistory] = useState<string[]>([]);
  const [pointer, setPointer] = useState<number>(-1); // -1 indicates fresh input

  const add = (entry: string) => {
    setHistory((h) => [...h, entry]);
    setPointer(-1);
  };

  const get = (idx: number) => history[history.length - 1 - idx] || '';

  const navigateUp = () => {
    let next = pointer + 1;
    if (next > history.length - 1) {
      next = history.length - 1;
    }
    setPointer(next);
    return get(next);
  };

  const navigateDown = () => {
    let next = pointer - 1;
    if (next < -1) next = -1;
    setPointer(next);
    return next === -1 ? '' : get(next);
  };

  return { add, navigateUp, navigateDown };
};
