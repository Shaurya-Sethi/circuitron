import React, { useEffect, useState } from 'react';
import { Text } from 'ink';
import axios from 'axios';

const BACKEND_URL = process.env.CIRCUITRON_BACKEND_URL || 'http://localhost:8000';

const App: React.FC = () => {
  const [message, setMessage] = useState('Connecting to backend...');

  useEffect(() => {
    axios
      .post(`${BACKEND_URL}/run`, { prompt: 'ping' })
      .then((res) => {
        setMessage(res.data.status ?? 'ok');
      })
      .catch(() => setMessage('Failed to connect'));
  }, []);

  return <Text>{message}</Text>;
};

export default App;
