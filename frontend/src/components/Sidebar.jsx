import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Upload, Clock, FileText, Shield, Settings, Menu, ChevronLeft } from 'lucide-react';

const navItems = [
  { label: 'Dashboard', to: '/', icon: Home },
  { label: 'Upload Documents', to: '/upload', icon: Upload },
  { label: 'Upload History', to: '/upload-history', icon: Clock },
  { label: 'Document Viewer', to: '/viewer', icon: FileText },
  {label: 'Audit Logs', to: '/audit', icon: Shield},


];

export default function Sidebar() {
  const location = useLocation();
  const initialIsMobile = typeof window !== 'undefined' ? window.innerWidth < 1024 : false;
  const [isCollapsed, setIsCollapsed] = useState(initialIsMobile);
  const isMobileRef = useRef(initialIsMobile);

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 1024;
      if (isMobileRef.current !== mobile) {
        isMobileRef.current = mobile;
        setIsCollapsed(mobile);
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const toggleSidebar = () => {
    setIsCollapsed((prev) => !prev);
  };

  return (
    <aside
      className={`relative flex h-full min-h-screen flex-col bg-white/90 font-['Roboto',_sans-serif] text-[#0B3D91] shadow-xl ring-1 ring-blue-100/60 transition-[width] duration-300 ease-in-out backdrop-blur-sm ${
        isCollapsed ? 'w-20' : 'w-72'
      }`}
    >
      <div className="flex items-center justify-between px-4 pb-4 pt-6">
        <div
          className={`flex items-center gap-3 rounded-2xl px-3 py-2 transition-all duration-200 ${
            isCollapsed ? 'bg-transparent px-0' : 'bg-[#0B3D91]/10'
          }`}
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#0B3D91] text-white shadow-lg shadow-blue-900/20">
            LV
          </div>
          <div
            className={`transition-all duration-200 ${
              isCollapsed ? 'pointer-events-none w-0 opacity-0' : 'w-auto opacity-100'
            }`}
          >
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#0B3D91]/70">LegalView</p>
            <p className="text-lg font-semibold text-[#0B3D91]">Contract Intelligence</p>
          </div>
        </div>
        <button
          type="button"
          onClick={toggleSidebar}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="flex h-10 w-10 items-center justify-center rounded-full bg-[#0B3D91]/10 text-[#0B3D91] transition-all duration-200 hover:bg-[#0B3D91]/20 hover:shadow-md"
        >
          {isCollapsed ? <Menu size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <nav className="mt-2 flex flex-1 flex-col gap-1 px-3 pb-6">
        {navItems.map(({ label, to, icon: Icon }) => {
          const isActive = location.pathname === to;

          return (
            <Link
              key={label}
              to={to}
              className={`group relative flex items-center rounded-2xl px-3 py-3 text-sm font-medium transition-all duration-200 ease-out ${
                isCollapsed ? 'justify-center' : 'gap-3'
              } ${
                isActive
                  ? 'bg-[#0B3D91]/15 text-[#0B3D91] shadow-inner ring-1 ring-[#0B3D91]/30'
                  : 'text-[#0B3D91]/80 hover:bg-[#0B3D91]/10 hover:text-[#0B3D91]'
              }`}
              title={label}
            >
              <span
                className={`flex h-9 w-9 items-center justify-center rounded-xl bg-white text-[#0B3D91] shadow-md shadow-blue-900/10 transition-all duration-200 group-hover:scale-105 ${
                  isActive ? 'ring-1 ring-[#0B3D91]/40' : ''
                }`}
              >
                <Icon size={20} />
              </span>
              <span
                className={`origin-left text-base transition-all duration-200 ${
                  isCollapsed ? 'pointer-events-none w-0 opacity-0' : 'w-auto opacity-100'
                }`}
              >
                {label}
              </span>
            </Link>
          );
        })}
      </nav>


    </aside>
  );
}
