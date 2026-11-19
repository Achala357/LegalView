import { useEffect, useState } from 'react';
import axios from 'axios';
import { FileText, FileIcon, Trash2 } from 'lucide-react';

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
    <div className="min-h-screen bg-gradient-to-br from-[#F8F9FA] via-white to-[#ECEFF1] px-4 py-10 font-['Roboto',sans-serif] text-slate-800">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex flex-col gap-2">
          <h2 className="text-[#0B3D91] text-2xl font-bold">Upload History</h2>
          <p className="text-sm text-slate-600">Review and manage documents ingested into LegalView.</p>
        </div>
        {uploads.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-slate-200 bg-white/80 p-6 text-center text-slate-500 shadow-sm">
            No uploads yet.
          </p>
        ) : (
          <ul className="space-y-4">
            {uploads.map((upload, idx) => {
              const isPdf = upload.original_name?.toLowerCase().endsWith('.pdf');
              const Icon = isPdf ? FileText : FileIcon;

              return (
                <li
                  key={idx}
                  className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-[#0B3D91]/40 hover:bg-[#0B3D91]/5"
                >
                  <div className="flex items-start gap-4">
                    <span className="mt-1 inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#0B3D91]/10 text-[#0B3D91]">
                      <Icon className="h-5 w-5" />
                    </span>
                    <div>
                      <p className="font-semibold text-slate-800">{upload.original_name}</p>
                      <p className="text-xs text-slate-500">Stored as: {upload.filename}</p>
                      <p className="text-xs text-slate-500">{upload.timestamp}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(upload.filename)}
                    className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium text-red-500 transition hover:bg-red-50 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-red-200"
                    title="Delete file"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
