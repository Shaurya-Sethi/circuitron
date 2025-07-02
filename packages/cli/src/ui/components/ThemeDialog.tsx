import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import { themeManager } from '../themes/themeManager';

export interface ThemeDialogProps {
  onClose: () => void;
}

const ThemeDialog: React.FC<ThemeDialogProps> = ({ onClose }) => {
  const themes = themeManager.listThemes();
  const [index, setIndex] = useState(0);

  useInput((input, key) => {
    if (key.upArrow) setIndex((i) => (i > 0 ? i - 1 : i));
    if (key.downArrow) setIndex((i) => (i < themes.length - 1 ? i + 1 : i));
    if (key.return) {
      themeManager.setActiveTheme(themes[index]);
      onClose();
    }
    if (key.escape) onClose();
  });

  return (
    <Box flexDirection="column" borderStyle="round" padding={1}>
      {themes.map((name, i) => (
        <Text key={name} inverse={i === index}>
          {name}
        </Text>
      ))}
    </Box>
  );
};

export default ThemeDialog;
