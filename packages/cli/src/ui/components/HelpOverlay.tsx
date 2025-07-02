import React from 'react';
import { Box, Text } from 'ink';

const HelpOverlay: React.FC = () => (
  <Box flexDirection="column" borderStyle="round" padding={1}>
    <Text bold>Commands:</Text>
    <Text>/help - show this help</Text>
    <Text>/theme - change theme</Text>
    <Text>/clear - clear messages</Text>
    <Text marginTop={1} bold>Shortcuts:</Text>
    <Text>Ctrl+A / Ctrl+E - move cursor start/end</Text>
    <Text>Ctrl+P / Ctrl+N - history</Text>
    <Text>Ctrl+L - clear screen</Text>
  </Box>
);

export default HelpOverlay;
