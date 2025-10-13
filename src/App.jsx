import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import UploadPage from './pages/UploadPage';
import ContractViewer from './pages/ContractViewer';
import ClauseExtractor from './pages/ClauseExtractor';
import RiskReport from './pages/RiskReport';
import Chatbot from './pages/Chatbot';
import LabelingTool from './pages/LabelingTool';
import SettingsPage from './pages/SettingsPage';
import UploadHistory from './pages/UploadHistory';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/viewer" element={<ContractViewer />} />
          <Route path="/clauses" element={<ClauseExtractor />} />
          <Route path="/risk" element={<RiskReport />} />
          <Route path="/qa" element={<Chatbot />} />
          <Route path="/labeling" element={<LabelingTool />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/upload-history" element={<UploadHistory />} />
        </Route>
      </Routes>
    </Router>
  );
}
