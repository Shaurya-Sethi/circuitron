export type CommandType = 'help' | 'theme' | 'clear';
export interface Command {
  type: CommandType;
  args?: string[];
}

export function parseCommand(input: string): Command | null {
  if (!input.startsWith('/')) return null;
  const parts = input.slice(1).trim().split(/\s+/);
  const name = parts[0];
  const args = parts.slice(1);
  if (name === 'help') return { type: 'help', args };
  if (name === 'theme') return { type: 'theme', args };
  if (name === 'clear') return { type: 'clear', args };
  return null;
}
