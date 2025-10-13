// src/pages/UploadPage.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';

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
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Upload Contract</h2>

      {/* Drag-and-drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-4 border-dashed border-gray-400 p-8 rounded-lg text-center mb-4 bg-white"
      >
        {file ? (
          <p className="text-green-600 font-semibold">{file.name}</p>
        ) : (
          <p className="text-gray-500">Drag and drop a file here</p>
        )}
      </div>

      {/* File input */}
      <input type="file" onChange={handleChange} className="mb-4" />

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={uploading}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        {uploading ? 'Uploading...' : 'Upload'}
      </button>

      {/* Message */}
      {message && <p className="mt-4 font-medium">{message}</p>}

      {/* Upload History */}
      <div className="mt-8">
        <h3 className="text-xl font-semibold mb-2">Upload History</h3>
        <ul className="space-y-2">
          {uploads.length === 0 ? (
            <p className="text-gray-500">No uploads yet.</p>
          ) : (
            uploads.map((item, index) => (
              <li key={index} className="bg-gray-100 p-3 rounded shadow-sm">
                <strong>{item.original_name}</strong>
                <br />
                <span className="text-sm text-gray-600">Saved as: {item.filename}</span>
                <br />
                <span className="text-sm text-gray-600">Time: {item.timestamp}</span>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
