export type BannerThemeName = 'electric' | 'solarizedDark' | 'sunset';

const themes: Record<BannerThemeName, string[]> = {
  electric: ['#FFFF66', '#CCFF66', '#66FFCC', '#66CCFF', '#4682B4'],
  solarizedDark: ['#002B36', '#586E75', '#839496', '#93A1A1', '#EEE8D5'],
  sunset: ['#FF7E5F', '#FEB47B'],
};

export function getBannerColors(name: string): string[] {
  if ((Object.keys(themes) as string[]).includes(name)) {
    return themes[name as BannerThemeName];
  }
  return themes.electric;
}
