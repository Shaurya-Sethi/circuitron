import React from 'react';
import { render } from 'ink';
import App from './ui/App';
import { themeManager } from './ui/themes/themeManager';

const argv = process.argv.slice(2);
const themeArgIndex = argv.indexOf('--theme');
const bannerThemeArgIndex = argv.indexOf('--banner-theme');

const themeName =
  (themeArgIndex !== -1 && argv[themeArgIndex + 1]) ||
  process.env.CIRCUITRON_THEME ||
  'dark';
themeManager.setActiveTheme(themeName);

if (bannerThemeArgIndex !== -1 && argv[bannerThemeArgIndex + 1]) {
  process.env.CIRCUITRON_BANNER_THEME = argv[bannerThemeArgIndex + 1];
}

render(<App />);
