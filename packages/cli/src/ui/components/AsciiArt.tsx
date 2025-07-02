import React from 'react';
import { Box, Text } from 'ink';
import gradient from 'gradient-string';
import { getBannerColors } from '../themes/bannerThemes';

const bannerArt = `
 ██████╗ ██╗██████╗  ██████╗██╗   ██╗██╗████████╗██████╗  ██████╗ ███╗   ██╗
██╔════╝ ██║██╔══██╗██╔════╝██║   ██║██║╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║
██║      ██║██████╔╝██║     ██║   ██║██║   ██║   ██████╔╝██║   ██║██╔██╗ ██║
██║      ██║██╔══██╗██║     ██║   ██║██║   ██║   ██╔══██╗██║   ██║██║╚██╗██║
╚██████╗ ██║██║  ██║╚██████╗╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
`;

export const AsciiArt: React.FC = () => {
  const themeName = process.env.CIRCUITRON_BANNER_THEME || 'electric';
  const colors = getBannerColors(themeName);

  return (
    <Box flexDirection="column" marginBottom={1}>
      {bannerArt
        .trim()
        .split('\n')
        .map((line, idx) => (
          <Text key={idx}>{gradient(colors)(line)}</Text>
        ))}
    </Box>
  );
};

export default AsciiArt;
