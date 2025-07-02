import { defaultTheme } from './defaultTheme';

class ThemeManager {
  private active = defaultTheme;

  getActive() {
    return this.active;
  }
}

export const themeManager = new ThemeManager();
