import axios from 'axios';
import { pingBackend } from '../src/ui/hooks/useBackend';

jest.mock('axios');
const mockedPost = axios.post as jest.Mock;

test('returns status from backend', async () => {
  mockedPost.mockResolvedValue({ data: { status: 'ok' } });
  const status = await pingBackend('http://localhost:8000');
  expect(status).toBe('ok');
});


test('throws on connection error', async () => {
  mockedPost.mockRejectedValue(new Error('fail'));
  await expect(pingBackend('http://localhost:8000')).rejects.toThrow('fail');
});
