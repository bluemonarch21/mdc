import React from 'react';

import { BrowserRouter, Route, Routes } from 'react-router-dom';

import HomePage from './pages/HomePage';
import TestPage from './pages/TestPage';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route index element={<HomePage />} />
        <Route path='test' element={<TestPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
