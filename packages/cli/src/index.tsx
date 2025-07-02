import React from 'react';
import { render } from 'ink';
import App from './ui/App';
import { themeManager } from './ui/themes/themeManager';

const themeName = process.env.CIRCUITRON_THEME || 'dark';
themeManager.setActiveTheme(themeName);

render(<App />);
