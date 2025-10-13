// src/components/Sidebar.jsx
import { Home, FileText, Settings, Upload, List, Shield, MessageCircle, Edit, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Sidebar() {
  return (
    <div className="w-64 h-screen bg-gray-900 text-white p-4">
      <h1 className="text-2xl font-bold mb-6">LegalView</h1>
      <nav className="space-y-4">
        <Link to="/" className="flex items-center gap-2 hover:text-blue-400">
          <Home size={20} /> Dashboard
        </Link>
        <Link to="/upload" className="flex items-center gap-2 hover:text-blue-400">
          <Upload size={20} /> Upload
        </Link>
        <Link to="/viewer" className="flex items-center gap-2 hover:text-blue-400">
          <FileText size={20} /> Viewer
        </Link>
        <Link to="/clauses" className="flex items-center gap-2 hover:text-blue-400">
          <List size={20} /> Clauses
        </Link>
        <Link to="/risk" className="flex items-center gap-2 hover:text-blue-400">
          <Shield size={20} /> Risk
        </Link>
        <Link to="/qa" className="flex items-center gap-2 hover:text-blue-400">
          <MessageCircle size={20} /> Q&A
        </Link>
        <Link to="/labeling" className="flex items-center gap-2 hover:text-blue-400">
          <Edit size={20} /> Labeling
        </Link>
        <Link to="/upload-history" className="flex items-center gap-2 hover:text-blue-400">
           <Clock size={20} /> Upload History
        </Link>
        <Link to="/settings" className="flex items-center gap-2 hover:text-blue-400">
          <Settings size={20} /> Settings
        </Link>
        

      </nav>
    </div>
  );
}
