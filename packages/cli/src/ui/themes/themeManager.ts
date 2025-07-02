import { defaultTheme } from './defaultTheme';
import { lightTheme } from './lightTheme';
import { sunsetTheme } from './sunsetTheme';

export type Theme = typeof defaultTheme;

class ThemeManager {
  private activeName: string;
  private active: Theme;
  private themes: Record<string, Theme> = {
    dark: defaultTheme,
    light: lightTheme,
    sunset: sunsetTheme,
  };
  private listeners: Array<() => void> = [];

  constructor() {
    const envTheme = process.env.CIRCUITRON_THEME || 'dark';
    if (this.themes[envTheme]) {
      this.activeName = envTheme;
      this.active = this.themes[envTheme];
    } else {
      this.activeName = 'dark';
      this.active = defaultTheme;
    }
  }

  getActive() {
    return this.active;
  }

  listThemes() {
    return Object.keys(this.themes);
  }

  setActiveTheme(name: string) {
    const theme = this.themes[name];
    if (theme) {
      this.active = theme;
      this.activeName = name;
      process.env.CIRCUITRON_THEME = name;
      this.listeners.forEach((l) => l());
    }
  }

  subscribe(listener: () => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }
}

export const themeManager = new ThemeManager();
