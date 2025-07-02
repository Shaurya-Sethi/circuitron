import React from 'react';

export enum StreamingState {
  Idle,
  Responding,
}

export const StreamingContext = React.createContext(StreamingState.Idle);
