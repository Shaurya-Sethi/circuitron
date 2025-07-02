import React, { useState } from 'react';

export enum StreamingState {
  Idle,
  Responding,
}

export interface StreamingContextValue {
  state: StreamingState;
  setState: (s: StreamingState) => void;
}

export const StreamingContext = React.createContext<StreamingContextValue>({
  state: StreamingState.Idle,
  setState: () => {},
});

export const StreamingProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, setState] = useState(StreamingState.Idle);
  return (
    <StreamingContext.Provider value={{ state, setState }}>
      {children}
    </StreamingContext.Provider>
  );
};

export const useStreamingContext = () => React.useContext(StreamingContext);
