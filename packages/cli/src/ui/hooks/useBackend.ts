import axios from 'axios';

export async function pingBackend(url: string) {
  const res = await axios.post(`${url}/run`, { prompt: 'ping' });
  return res.data.status as string;
}
