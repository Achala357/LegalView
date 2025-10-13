import { useEffect, useState } from 'react';
import axios from 'axios';

export default function UploadHistory() {
  const [uploads, setUploads] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:8000/api/uploads')
      .then(res => setUploads(res.data))
      .catch(err => console.error(err));
  }, []);

  const handleDelete = async (filename) => {
    const confirmed = window.confirm(`Are you sure you want to delete "${filename}"?`);
    if (!confirmed) return;
  
    try {
      await axios.delete(`http://localhost:8000/api/uploads/${encodeURIComponent(filename)}`);
      setUploads(prev => prev.filter(upload => upload.filename !== filename));
    } catch (err) {
      console.error('Delete error:', err);
      alert('Failed to delete the file.');
    }
  };
  
  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Upload History</h2>
      {uploads.length === 0 ? (
        <p className="text-gray-500">No uploads yet.</p>
      ) : (
        <ul className="space-y-2">
          {uploads.map((upload, idx) => (
            <li key={idx} className="bg-white p-4 rounded shadow flex justify-between items-center">
            <div>
              <p><strong>{upload.original_name}</strong></p>
              <p className="text-sm text-gray-500">{upload.timestamp}</p>
            </div>
            <button
              onClick={() => handleDelete(upload.filename)}
              className="text-red-600 hover:text-red-800 text-sm ml-4"
              title="Delete file"
            >
               Delete
            </button>
          </li>
          
          ))}
        </ul>
      )}
    </div>
  );
}
