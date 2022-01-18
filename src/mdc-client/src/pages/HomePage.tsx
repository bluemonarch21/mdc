import React from 'react';

import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <div>
      <p>Hi, Hello</p>
      <Link to={'/test'}>Go to TestPage</Link>
      <p> <a href={'/admin'}>Go to Django Admin</a> </p>
    </div>
  );
};

export default HomePage;
