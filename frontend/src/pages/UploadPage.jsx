// src/pages/UploadPage.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud } from 'lucide-react';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [uploads, setUploads] = useState([]);

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    setFile(droppedFile);
  };

  const handleChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    setMessage('');

    try {
      await axios.post('http://localhost:8000/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage('Upload successful!');
      setFile(null);
      fetchUploads(); // Refresh list after upload
    } catch (err) {
      console.error(err);
      setMessage('Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const fetchUploads = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/uploads');
      setUploads(res.data.reverse()); // Show latest first
    } catch (err) {
      console.error('Failed to fetch uploads:', err);
    }
  };

  useEffect(() => {
    fetchUploads();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8F9FA] via-white to-[#ECEFF1] px-4 py-10 font-['Roboto',sans-serif] text-slate-800">
      <div className="max-w-3xl mx-auto space-y-8">
        <header className="space-y-2">
          <p className="text-sm uppercase tracking-wide text-[#0B3D91]/70">Document Intake</p>
          <h2 className="text-3xl font-bold text-[#0B3D91]">Upload Contract</h2>
          <p className="text-sm text-slate-600">Securely ingest new agreements for LegalView analysis.</p>
        </header>

        <div className="rounded-2xl border border-slate-200/60 bg-white/90 shadow-xl backdrop-blur-sm">
          <div className="p-8 space-y-6">
            <div className="flex items-center justify-center">
              <span className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-[#0B3D91]/10 text-[#0B3D91]">
                <UploadCloud className="h-8 w-8 animate-pulse" />
              </span>
            </div>
            <h3 className="text-[#0B3D91] text-xl font-semibold text-center">Select or Drag Files</h3>

            {/* Drag-and-drop zone */}
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              className="group relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-[#0B3D91]/40 bg-gradient-to-br from-white via-white to-[#F8F9FA] p-8 text-center transition hover:border-[#0B3D91] hover:shadow-lg"
            >
              {file ? (
                <p className="text-[#34A853] font-semibold">{file.name}</p>
              ) : (
                <p className="text-slate-500">
                  Drag and drop your contract here or use the button below
                </p>
              )}
            </div>

            {/* File input */}
            <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-between">
              <label className="text-sm font-medium text-slate-600" htmlFor="contract-upload">
                Choose a file from your device
              </label>
              <input
                id="contract-upload"
                type="file"
                onChange={handleChange}
                className="w-full cursor-pointer rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm transition focus:border-[#0B3D91] focus:outline-none focus:ring-2 focus:ring-[#0B3D91]/40 sm:w-auto"
              />
            </div>

            {/* Upload button */}
            <div className="flex justify-end">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="inline-flex items-center justify-center rounded-full bg-[#0B3D91] px-6 py-2 text-sm font-semibold text-white shadow-md transition hover:bg-[#082d6b] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#0B3D91] disabled:cursor-not-allowed disabled:bg-[#0B3D91]/60"
              >
                {uploading ? 'Uploading…' : 'Upload File'}
              </button>
            </div>

            {/* Message */}
            {message && (
              <p className="rounded-lg bg-[#34A853]/10 px-4 py-2 text-sm font-medium text-[#1f7a3b]">
                {message}
              </p>
            )}
          </div>
        </div>

        {/* Upload History */}
        <section className="space-y-4">
          <h3 className="text-[#0B3D91] text-xl font-semibold">Recent Uploads</h3>
          <ul className="space-y-3">
            {uploads.length === 0 ? (
              <p className="rounded-xl border border-dashed border-slate-200 bg-white/70 p-6 text-center text-slate-500">
                No uploads yet.
              </p>
            ) : (
              uploads.map((item, index) => (
                <li
                  key={index}
                  className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm transition hover:border-[#0B3D91]/40 hover:bg-[#0B3D91]/5"
                >
                  <strong className="text-slate-800">{item.original_name}</strong>
                  <div className="mt-1 text-xs text-slate-500">
                    <p>Saved as: {item.filename}</p>
                    <p>Time: {item.timestamp}</p>
                  </div>
                </li>
              ))
            )}
          </ul>
        </section>
      </div>
    </div>
  );
}
