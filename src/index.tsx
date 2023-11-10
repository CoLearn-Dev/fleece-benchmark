import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter as Router, Route, Routes, useParams } from 'react-router-dom';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <Router>
      <React.StrictMode>
        <Routes>
          <Route path="/:id" element={<AppWithId />}/>
          <Route path="/" element={<App tid={"null"} />} />
        </Routes>
      </React.StrictMode>
  </Router>
);

function AppWithId() {
  let { id } = useParams();
  return <App tid={id ?? "null"} />;
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
