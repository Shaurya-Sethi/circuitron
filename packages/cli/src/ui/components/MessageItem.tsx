import React from 'react';
import { Box, Text } from 'ink';
import Markdown from 'ink-markdown';
import { highlight } from 'cli-highlight';

export interface MessageItemProps {
  from: 'user' | 'backend';
  message: string;
}

const MessageItem: React.FC<MessageItemProps> = ({ from, message }) => {
  const highlightCode = (code: string) => highlight(code, { language: 'plaintext', ignoreIllegals: true });

  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text color={from === 'user' ? 'green' : 'blue'}>{from === 'user' ? '> ' : '✦ '}</Text>
      <Box marginLeft={2} width="100%">
        <Markdown code={highlightCode}>{message}</Markdown>
      </Box>
    </Box>
  );
};

export default MessageItem;
