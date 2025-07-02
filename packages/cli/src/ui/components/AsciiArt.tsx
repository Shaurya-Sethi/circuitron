import React from 'react';
import { Text, Box, useStdout } from 'ink';
import { themeManager } from '../themes/themeManager';

const shortArt = `
 ___ ___ ___  ___ _   _ ___ _____ ___  ___  _  _
/ __|_ _| _ \/ __| | | |_ _|_   _| _ \/ _ \| \| |
\__ \| ||   / (__| |_| || |  | | |   / (_) | .\` |
|___/___|_|_\\___|\___/|___| |_| |_|_\\___/|_|\_|
`;

const longArt = `
  ____ ___ ____   ____ _   _ ___ _____ ____   ___  _   _
 / ___|_ _|  _ \ / ___| | | |_ _|_   _|  _ \ / _ \| \ | |
| |    | || |_) | |   | | | || |  | | | |_) | | | |  \| |
| |___ | ||  _ <| |___| |_| || |  | | |  _ <| |_| | |\  |
 \____|___|_| \_\\____|\___/|___| |_| |_| \_\\___/|_| \_|
`;

export const AsciiArt: React.FC = () => {
  const { stdout } = useStdout();
  const width = stdout?.columns ?? 80;
  const art = width < 80 ? shortArt : longArt;
  const theme = themeManager.getActive();
  const warmColors = ['#ff7f50', '#ff8c00', '#ff9d00', '#ff7043', '#ff5722'];

  return (
    <Box flexDirection="column" marginBottom={1}>
      {art
        .trim()
        .split("\n")
        .map((line, idx) => (
          <Text key={idx} color={warmColors[idx % warmColors.length] || theme.Foreground}>
            {line}
          </Text>
        ))}
    </Box>
  );
};

export default AsciiArt;
