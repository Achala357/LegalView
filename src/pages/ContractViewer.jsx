// src/pages/ContractViewer.jsx
import { useEffect, useState } from 'react';
import axios from 'axios';
import { Document as PDFDocument, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker?url';

pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorker;





export default function ContractViewer() {
  const [uploads, setUploads] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [content, setContent] = useState('');
  const [numPages, setNumPages] = useState(null);
  const [pdfBlob, setPdfBlob] = useState(null);


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
        console.error("Failed to fetch PDF blob:", err);
      }
    };
  
    if (selectedFile?.endsWith('.pdf')) {
      fetchPDFBlob();
    }
  }, [selectedFile]);
  

  const handleFileSelect = async (filename) => {
    console.log("Selected file:", filename);
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
    <div className="max-w-5xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Contract Viewer</h2>

      <div className="flex gap-4 mb-6">
        {/* File List */}
        <div className="w-1/3 bg-white border rounded shadow-sm p-4">
          <h3 className="text-lg font-semibold mb-4 border-b pb-2">Uploaded Files</h3>
          <ul className="space-y-2 overflow-y-auto max-h-[28rem] text-sm">
            {uploads.map((file, idx) => (
              <li
                key={idx}
                onClick={() => handleFileSelect(file.filename)} // ✅ correct full name
                className={`cursor-pointer p-2 rounded ${
                  selectedFile === file.filename ? 'bg-blue-200 font-semibold' : 'hover:bg-gray-100'
                }`}
              >
                {file.original_name}
              </li>
            ))}
          </ul>
        </div>

        {/* File Viewer */}
        <div className="w-2/3 bg-white border rounded shadow-sm p-4">
          <h3 className="text-lg font-semibold mb-4 border-b pb-2">File Content</h3>
          {selectedFile && (
  <div className="mb-3 flex gap-3 items-center">
    <a
      href={`http://localhost:8000/uploads/${encodeURIComponent(selectedFile)}`}
      target="_blank"
      rel="noopener noreferrer"
      className="bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700 transition"
    >
      Preview in New Tab
    </a>
    <a
      href={`http://localhost:8000/uploads/${encodeURIComponent(selectedFile)}`}
      download
      className="bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 transition"
    >
      Download
    </a>
  </div>
)}

          <div className="overflow-y-auto max-h-[32rem] whitespace-pre-wrap text-sm font-mono text-gray-800">
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
                      <Page key={`page_${index + 1}`} pageNumber={index + 1} />
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
  );
}
