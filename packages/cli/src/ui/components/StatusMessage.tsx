import React from 'react';
import { Text } from 'ink';

export interface StatusMessageProps {
  message: string;
}

export const StatusMessage: React.FC<StatusMessageProps> = ({ message }) => (
  <Text>{message}</Text>
);
