import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import { useInputHistory } from '../hooks/useInputHistory';
import { parseCommand, Command } from '../commandProcessor';

export interface InputPromptProps {
  onSubmit: (text: string, shell: boolean) => void;
  onCommand: (cmd: Command) => void;
  onClearScreen: () => void;
}

const InputPrompt: React.FC<InputPromptProps> = ({
  onSubmit,
  onCommand,
  onClearScreen,
}) => {
  const [buffer, setBuffer] = useState('');
  const [cursor, setCursor] = useState(0);
  const [shell, setShell] = useState(false);
  const history = useInputHistory();

  useInput((input, key) => {
    if (key.ctrl && input === 'a') setCursor(0);
    else if (key.ctrl && input === 'e') setCursor(buffer.length);
    else if (key.ctrl && input === 'l') onClearScreen();
    else if (key.ctrl && input === 'p') {
      const entry = history.navigateUp();
      setBuffer(entry);
      setCursor(entry.length);
    } else if (key.ctrl && input === 'n') {
      const entry = history.navigateDown();
      setBuffer(entry);
      setCursor(entry.length);
    } else if (key.return && !key.ctrl) {
      if (buffer.startsWith('/')) {
        const cmd = parseCommand(buffer);
        if (cmd) onCommand(cmd);
      } else {
        onSubmit(buffer, shell);
        history.add(buffer);
      }
      setBuffer('');
      setCursor(0);
      setShell(false);
    } else if (key.return && key.ctrl) {
      setBuffer((b) => b + '\n');
      setCursor((c) => c + 1);
    } else if (key.leftArrow) setCursor((c) => Math.max(0, c - 1));
    else if (key.rightArrow) setCursor((c) => Math.min(buffer.length, c + 1));
    else if (key.backspace || key.delete) {
      if (cursor > 0) {
        setBuffer(buffer.slice(0, cursor - 1) + buffer.slice(cursor));
        setCursor(cursor - 1);
      }
    } else if (input === '!' && buffer.length === 0) {
      setShell((s) => !s);
    } else if (!key.ctrl && input) {
      setBuffer(buffer.slice(0, cursor) + input + buffer.slice(cursor));
      setCursor(cursor + input.length);
    }
  });

  return (
    <Box borderStyle="round" paddingX={1}>
      <Text color={shell ? 'yellow' : 'cyan'}>{shell ? '! ' : '> '}</Text>
      <Text>
        {buffer.slice(0, cursor)}
        <Text inverse>{buffer[cursor] || ' '}</Text>
        {buffer.slice(cursor + 1)}
      </Text>
    </Box>
  );
};

export default InputPrompt;
