import React from 'react';

import { render } from '@testing-library/react';

import App from './App';

describe('dummy test', () => {
  test('should render App', () => {
    render(<App />);
  });
});
