import React, { useEffect, useState } from 'react';
import { pingBackend } from '../hooks/useBackend';

export interface BackendState {
  connected: boolean;
}

export const BackendContext = React.createContext<BackendState>({
  connected: false,
});

interface BackendProviderProps {
  url: string;
  children: React.ReactNode;
}

export const BackendProvider: React.FC<BackendProviderProps> = ({ url, children }) => {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    pingBackend(url)
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, [url]);

  return (
    <BackendContext.Provider value={{ connected }}>
      {children}
    </BackendContext.Provider>
  );
};

export const useBackendContext = () => React.useContext(BackendContext);
