import React from 'react';
import { Text } from 'ink';
import Spinner from 'ink-spinner';
import { useStreamingContext, StreamingState } from '../contexts/StreamingContext';

const LoadingIndicator: React.FC = () => {
  const { state } = useStreamingContext();
  if (state === StreamingState.Responding) {
    return (
      <Text color="cyan">
        <Spinner type="dots" />
      </Text>
    );
  }
  return null;
};

export default LoadingIndicator;
