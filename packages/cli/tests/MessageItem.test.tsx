import React from 'react';
import TestRenderer from 'react-test-renderer';
import MessageItem from '../src/ui/components/MessageItem';

jest.mock('ink', () => {
  const React = require('react');
  return {
    Box: (props: any) => React.createElement('Box', props, props.children),
    Text: (props: any) => React.createElement('Text', props, props.children),
  };
});

test('renders without crashing', () => {
  TestRenderer.act(() => {
    TestRenderer.create(
      <MessageItem from="backend" message={'`code`'} />
    );
  });
});
