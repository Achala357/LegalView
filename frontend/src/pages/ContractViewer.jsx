// src/pages/ContractViewer.jsx
import { useEffect, useState } from 'react';
import axios from 'axios';
import { Document as PDFDocument, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { ArrowLeft, Download, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';


pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorker;

export default function ContractViewer() {
  const [uploads, setUploads] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [content, setContent] = useState('');
  const [numPages, setNumPages] = useState(null);
  const [pdfBlob, setPdfBlob] = useState(null);
  const navigate = useNavigate();


  useEffect(() => {
    const fetchUploads = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/uploads');
        setUploads(res.data.reverse());
      } catch (err) {
        console.error('Failed to load uploads:', err);
      }
    };
    fetchUploads();
  }, []);

  useEffect(() => {
    const fetchPDFBlob = async () => {
      try {
        const res = await fetch(`http://localhost:8000/uploads/${encodeURIComponent(selectedFile)}`);
        const blob = await res.blob();
        setPdfBlob(blob);
      } catch (err) {
        console.error('Failed to fetch PDF blob:', err);
      }
    };

    if (selectedFile?.endsWith('.pdf')) {
      fetchPDFBlob();
    }
  }, [selectedFile]);

  const handleFileSelect = async (filename) => {
    console.log('Selected file:', filename);
    setSelectedFile(filename);
    setContent('');
    setPdfBlob(null);
    setNumPages(null);

    if (filename.endsWith('.pdf')) {
      // Do not fetch content for PDFs
      return;
    }

    try {
      const res = await axios.get(`http://localhost:8000/api/file/${encodeURIComponent(filename)}`);
      setContent(res.data.content);
    } catch (err) {
      console.error('Error loading file:', err);
      setContent('Could not load file content.');
    }
  };

  const onPDFLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8F9FA] via-white to-[#ECEFF1] px-4 py-10 font-['Roboto',sans-serif] text-slate-800">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="flex flex-col gap-2">
          <p className="text-sm uppercase tracking-wide text-[#0B3D91]/70">LegalView Intelligence</p>
          <h2 className="text-3xl font-bold text-[#0B3D91]">Contract Viewer</h2>
          <p className="text-sm text-slate-600">Review, download, and analyse agreements in a secure workspace.</p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[320px,1fr]">
          {/* File List */}
          <div className="rounded-2xl border border-slate-200 bg-white/90 shadow-lg backdrop-blur-sm">
            <div className="border-b border-slate-200/60 px-6 py-4">
              <h3 className="text-lg font-semibold text-[#0B3D91]">Uploaded Files</h3>
            </div>
            <ul className="max-h-[28rem] space-y-2 overflow-y-auto px-4 py-4 text-sm">
              {uploads.map((file, idx) => (
                <li
                  key={idx}
                  onClick={() => handleFileSelect(file.filename)}
                  className={`cursor-pointer rounded-xl px-4 py-3 transition ${
                    selectedFile === file.filename
                      ? 'bg-[#0B3D91]/10 font-semibold text-[#0B3D91] shadow-inner'
                      : 'text-slate-700 hover:bg-[#0B3D91]/5'
                  }`}
                >
                  <p className="truncate">{file.original_name}</p>
                  <p className="text-xs text-slate-400">{file.timestamp}</p>
                </li>
              ))}
            </ul>
          </div>

          {/* File Viewer */}
          <div className="flex flex-col rounded-2xl border border-slate-200 bg-white/95 p-6 shadow-xl backdrop-blur-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-[#0B3D91]/5 px-4 py-3">
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-wide text-[#0B3D91]/70">Currently Viewing</p>
                <h3 className="truncate text-lg font-semibold text-[#0B3D91]">
                  {selectedFile ? selectedFile : 'Select a document'}
                </h3>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => window.history.back()}
                  className="inline-flex items-center gap-1 rounded-full border border-transparent bg-white px-4 py-2 text-sm font-semibold text-[#0B3D91] shadow-sm transition hover:bg-[#0B3D91]/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#0B3D91]"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </button>
                {selectedFile && (
                  <a
                    href={`http://localhost:8000/uploads/${encodeURIComponent(selectedFile)}`}
                    download
                    className="inline-flex items-center gap-1 rounded-full border border-[#0B3D91]/70 bg-[#0B3D91] px-4 py-2 text-sm font-semibold text-white shadow-md transition hover:bg-[#082d6b] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#0B3D91]"
                  >
                    <Download className="h-4 w-4" />
                    Download
                  </a>
                )}
                {selectedFile && (
                  <a
                    href={`http://localhost:8000/uploads/${encodeURIComponent(selectedFile)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 rounded-full border border-transparent bg-white px-4 py-2 text-sm font-semibold text-[#0B3D91] shadow-sm transition hover:bg-[#0B3D91]/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#0B3D91]"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Open in New Tab
                  </a>
                )}
              </div>
            </div>
            {selectedFile && (
  <button
    onClick={() =>
      navigate(`/analysis/${encodeURIComponent(selectedFile)}`)
    }
    className="inline-flex items-center gap-1 rounded-full border border-[#0B3D91]/70 bg-white px-4 py-2 text-sm font-semibold text-[#0B3D91] shadow-sm transition hover:bg-[#0B3D91]/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#0B3D91]"
  >
    Analyse
  </button>
)}


            <div className="mt-4 flex-1 overflow-hidden rounded-xl border border-dashed border-slate-200">
              <div className="h-[80vh] overflow-auto px-6 py-6 text-sm leading-relaxed text-slate-700">
                {selectedFile ? (
                  selectedFile.endsWith('.pdf') ? (
                    pdfBlob ? (
                      <PDFDocument
                        file={pdfBlob}
                        onLoadSuccess={onPDFLoadSuccess}
                        onLoadError={(error) => {
                          console.error('PDF load error:', error);
                          alert(`PDF load error: ${error.message}`);
                        }}
                        loading="Loading PDF..."
                      >
                        {Array.from(new Array(numPages), (el, index) => (
                          <Page key={`page_${index + 1}`} pageNumber={index + 1} className="mb-6 rounded-lg border border-slate-200 shadow-sm" />
                        ))}
                      </PDFDocument>
                    ) : (
                      'Loading PDF...'
                    )
                  ) : (
                    content || 'Loading content...'
                  )
                ) : (
                  'Select a file to view its content.'
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
