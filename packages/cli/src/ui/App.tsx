import React from 'react';
import { Box, Text } from 'ink';
import AsciiArt from './components/AsciiArt';
import { BackendProvider, useBackendContext } from './contexts/BackendContext';

const BACKEND_URL = process.env.CIRCUITRON_BACKEND_URL || 'http://localhost:8000';

const Status: React.FC = () => {
  const { connected } = useBackendContext();
  return <Text>{connected ? 'Connected to backend' : 'Failed to connect'}</Text>;
};

const App: React.FC = () => (
  <BackendProvider url={BACKEND_URL}>
    <Box flexDirection="column">
      <AsciiArt />
      <Status />
    </Box>
  </BackendProvider>
);

export default App;
