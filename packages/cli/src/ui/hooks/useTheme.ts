import { useSyncExternalStore } from 'react';
import { themeManager, Theme } from '../themes/themeManager';

export const useTheme = (): Theme => {
  return useSyncExternalStore(
    (listener) => themeManager.subscribe(listener),
    () => themeManager.getActive()
  );
};
