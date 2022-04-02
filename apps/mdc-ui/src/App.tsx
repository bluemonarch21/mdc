import React from 'react';
import './styles.scss';

import { BrowserRouter, Route, Routes } from 'react-router-dom';

import HomePage from './pages/HomePage';
import TestPage from './pages/TestPage';
// import LoadingPage from './pages/LoadingPage';
// import ResultPage from './pages/ResultPage';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route index element={<HomePage />} />
        <Route path='test' element={<TestPage />} />
        {/*<Route path='loading' element={<LoadingPage />} />*/}
        {/*<Route path='result' element={<ResultPage />} />*/}
      </Routes>
    </BrowserRouter>
  );
};

export default App;
