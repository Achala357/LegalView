// src/pages/Dashboard.jsx
import {
  CalendarCheck,
  ChevronRight,
  FileText,
  LineChart,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8F9FA] via-white to-[#ECEFF1] font-['Roboto',sans-serif] text-slate-900">
      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:space-y-12 lg:px-8">
        <header className="rounded-lg border border-slate-200 bg-white/90 shadow-md backdrop-blur-sm transition duration-200 hover:shadow-lg">
          <div className="flex flex-col gap-6 p-6 sm:p-8 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-wider text-[#0B3D91]/80">
                LegalView Intelligence
              </p>
              <h1 className="text-3xl font-bold text-[#0B3D91] sm:text-4xl">
                Welcome to the LegalView Dashboard
              </h1>
              <p className="max-w-2xl text-sm leading-relaxed text-slate-600 sm:text-base">
                Monitor contract risk, streamline document reviews, and stay ahead of
                compliance milestones with a clear, modern command center.
              </p>
            </div>
            <button className="inline-flex items-center justify-center gap-2 rounded-lg border border-[#0B3D91] bg-[#0B3D91] px-5 py-3 text-sm font-semibold text-white shadow-sm transition duration-200 hover:-translate-y-0.5 hover:bg-blue-900 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0B3D91]/40">
              Review Upcoming Deadlines
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </header>




      </div>
    </div>
  );
}
