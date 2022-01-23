import React from 'react';

import { Link } from 'react-router-dom';

const TestPage: React.FC = () => {
  return (
    <div>
      <p>Hello, Test, Test</p>
      <Link to={'/'}>Back to HomePage</Link>
    </div>
  );
};

export default TestPage;
