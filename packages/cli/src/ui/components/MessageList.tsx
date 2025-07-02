import React from 'react';
import { Box } from 'ink';
import MessageItem from './MessageItem';

export interface Message {
  from: 'user' | 'backend';
  text: string;
}

export interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => (
  <Box flexDirection="column" marginBottom={1}>
    {messages.map((m, idx) => (
      <MessageItem key={idx} from={m.from} message={m.text} />
    ))}
  </Box>
);

export default MessageList;
