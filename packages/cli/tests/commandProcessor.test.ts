import { parseCommand } from '../src/ui/commandProcessor';

test('parse /help', () => {
  const cmd = parseCommand('/help');
  expect(cmd).toEqual({ type: 'help', args: [] });
});

test('parse /theme dark', () => {
  const cmd = parseCommand('/theme dark');
  expect(cmd).toEqual({ type: 'theme', args: ['dark'] });
});

test('non command', () => {
  const cmd = parseCommand('hello');
  expect(cmd).toBeNull();
});
