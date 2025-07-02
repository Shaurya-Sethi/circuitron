import React, { useState } from 'react';
import { Box, Text } from 'ink';
import AsciiArt from './components/AsciiArt';
import ThemeDialog from './components/ThemeDialog';
import InputPrompt from './components/InputPrompt';
import MessageList, { Message } from './components/MessageList';
import HelpOverlay from './components/HelpOverlay';
import LoadingIndicator from './components/LoadingIndicator';
import { BackendProvider, useBackendContext } from './contexts/BackendContext';
import { StreamingProvider } from './contexts/StreamingContext';
import { Command } from './commandProcessor';

const BACKEND_URL = process.env.CIRCUITRON_BACKEND_URL || 'http://localhost:8000';

const Status: React.FC = () => {
  const { connected } = useBackendContext();
  return <Text>{connected ? 'Connected to backend' : 'Failed to connect'}</Text>;
};

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [showHelp, setShowHelp] = useState(false);
  const [showTheme, setShowTheme] = useState(false);

  const handleSubmit = (text: string) => {
    setMessages((m) => [...m, { from: 'user', text }]);
    setMessages((m) => [...m, { from: 'backend', text: `Echo: ${text}` }]);
  };

  const handleCommand = (cmd: Command) => {
    if (cmd.type === 'help') setShowHelp((v) => !v);
    if (cmd.type === 'theme') setShowTheme(true);
    if (cmd.type === 'clear') setMessages([]);
  };

  return (
    <StreamingProvider>
      <BackendProvider url={BACKEND_URL}>
        <Box flexDirection="column">
          <AsciiArt />
          <Status />
          {showHelp && <HelpOverlay />}
          {showTheme && (
            <ThemeDialog
              onClose={() => setShowTheme(false)}
            />
          )}
          <MessageList messages={messages} />
          <LoadingIndicator />
          <InputPrompt
            onSubmit={handleSubmit}
            onCommand={handleCommand}
            onClearScreen={() => setMessages([])}
          />
        </Box>
      </BackendProvider>
    </StreamingProvider>
  );
};

export default App;
