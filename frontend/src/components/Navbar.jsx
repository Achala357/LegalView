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

        </nav>

      </div>
      <nav className="flex w-full items-center gap-2 px-4 pb-3 pt-2 sm:px-6 lg:hidden">

      </nav>
    </header>
  );
}
