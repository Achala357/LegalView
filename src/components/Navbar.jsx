// src/components/Navbar.jsx
import { LayoutDashboard, UploadCloud, Clock, Eye } from 'lucide-react';

const navItems = [
  { label: 'Overview', icon: LayoutDashboard, active: true },
  { label: 'Upload Center', icon: UploadCloud },
  { label: 'Recent Activity', icon: Clock },
  { label: 'Document Viewer', icon: Eye },
];

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 w-full bg-[#0B3D91] shadow-lg">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-2 text-white">
          <span className="text-lg font-semibold tracking-wide sm:text-xl">LegalView Intelligence</span>
        </div>
        <nav className="ml-6 hidden flex-1 items-center justify-evenly lg:flex">
          {navItems.map(({ label, icon: Icon, active }) => (
            <button
              key={label}
              type="button"
              className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium tracking-wide transition-colors duration-150 ease-in-out shadow-sm ${
                active
                  ? 'bg-white text-[#0B3D91] shadow-[0_4px_12px_rgba(0,0,0,0.12)]'
                  : 'text-white hover:bg-white/20'
              }`}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3 text-white">
          <div className="hidden text-sm font-medium tracking-wide sm:block">Welcome, Achala</div>
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-sm font-semibold uppercase">
            A
          </div>
        </div>
      </div>
      <nav className="flex w-full items-center gap-2 px-4 pb-3 pt-2 sm:px-6 lg:hidden">
        {navItems.map(({ label, icon: Icon, active }) => (
          <button
            key={label}
            type="button"
            className={`flex flex-1 items-center justify-center gap-2 rounded-full px-3 py-2 text-xs font-medium tracking-wide transition-colors duration-150 ease-in-out ${
              active
                ? 'bg-white text-[#0B3D91] shadow-[0_4px_12px_rgba(0,0,0,0.12)]'
                : 'text-white hover:bg-white/20'
            }`}
          >
            <Icon size={16} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </header>
  );
}
  