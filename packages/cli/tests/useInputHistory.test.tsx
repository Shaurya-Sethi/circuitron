import React from 'react';
import TestRenderer from 'react-test-renderer';
import { useInputHistory } from '../src/ui/hooks/useInputHistory';

test('history navigation', () => {
  let history: any = null;
  const TestComp = () => {
    history = useInputHistory();
    return null;
  };
  TestRenderer.act(() => {
    TestRenderer.create(<TestComp />);
  });
  if (!history) throw new Error('hook not initialized');
  TestRenderer.act(() => {
    history.add('first');
    history.add('second');
  });
  TestRenderer.act(() => {
    expect(history.navigateUp()).toBe('second');
  });
  TestRenderer.act(() => {
    expect(history.navigateUp()).toBe('first');
  });
  TestRenderer.act(() => {
    expect(history.navigateDown()).toBe('second');
  });
});
