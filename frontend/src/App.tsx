import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import DataQueryPage from './pages/DataQueryPage';
import DatasetManagementPage from './pages/DatasetManagementPage';
import ChartConsolePage from './pages/ChartConsolePage';

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <Routes>
          <Route path="/" element={<DataQueryPage />} />
          <Route path="/datasets" element={<DatasetManagementPage />} />
          <Route path="/visualize" element={<ChartConsolePage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
