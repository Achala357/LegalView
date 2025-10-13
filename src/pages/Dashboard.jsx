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

        <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {[{ icon: FileText, title: "Active Contracts", value: "128", trend: "+12%" }, { icon: ShieldCheck, title: "Compliance Score", value: "96", trend: "Stable" }, { icon: LineChart, title: "Risk Alerts", value: "5", trend: "-3 this week" }, { icon: CalendarCheck, title: "Upcoming Renewals", value: "9", trend: "Next 30 days" }].map(
            ({ icon: Icon, title, value, trend }) => (
              <article
                key={title}
                className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <div className="rounded-full bg-[#0B3D91]/10 p-2 text-[#0B3D91]">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-wide text-[#34A853]">
                    {trend}
                  </span>
                </div>
                <div className="mt-6 space-y-2">
                  <p className="text-sm font-medium text-slate-500">{title}</p>
                  <p className="text-3xl font-semibold text-slate-900">{value}</p>
                </div>
              </article>
            ),
          )}
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[#0B3D91]">Recent Activity</h2>
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Today
              </span>
            </div>
            <ul className="mt-6 space-y-5">
              {["Contract review completed for Apex Corp.", "Risk score updated for Global Holdings.", "Three documents added to M&A folder."].map(
                (item) => (
                  <li
                    key={item}
                    className="group flex items-start gap-3 rounded-md border border-transparent p-3 transition duration-200 hover:border-[#0B3D91]/30 hover:bg-[#0B3D91]/5"
                  >
                    <span className="mt-1 h-2 w-2 rounded-full bg-[#34A853]" aria-hidden />
                    <p className="text-sm text-slate-600 group-hover:text-slate-900">
                      {item}
                    </p>
                  </li>
                ),
              )}
            </ul>
            <button className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[#0B3D91] transition duration-200 hover:text-blue-900">
              View all updates
              <ChevronRight className="h-4 w-4" />
            </button>
          </article>

          <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md">
            <h2 className="text-lg font-semibold text-[#0B3D91]">Risk Overview</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              Track emerging concerns across your portfolio and prioritize reviews to
              maintain a proactive legal posture.
            </p>
            <div className="mt-5 space-y-4">
              {[{ label: "Data Privacy", status: "Low", color: "text-[#34A853]" }, { label: "Vendor Agreements", status: "Moderate", color: "text-amber-500" }, { label: "Regulatory Filings", status: "Elevated", color: "text-red-500" }].map(
                ({ label, status, color }) => (
                  <div
                    key={label}
                    className="flex items-center justify-between rounded-md border border-slate-100 bg-[#F8F9FA] p-4 transition duration-200 hover:border-[#0B3D91]/30 hover:bg-white"
                  >
                    <div>
                      <p className="text-sm font-semibold text-slate-700">{label}</p>
                      <p className="text-xs text-slate-500">Status</p>
                    </div>
                    <span className={`text-sm font-semibold ${color}`}>{status}</span>
                  </div>
                ),
              )}
            </div>
          </article>

          <article className="flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md">
            <div>
              <h2 className="text-lg font-semibold text-[#0B3D91]">Quick Actions</h2>
              <p className="mt-3 text-sm text-slate-600">
                Accelerate your workflow with streamlined tasks tailored to your caseload.
              </p>
            </div>
            <div className="mt-6 space-y-3">
              {[{ icon: UploadCloud, label: "Upload new contract" }, { icon: ShieldCheck, label: "Run compliance scan" }, { icon: FileText, label: "Generate summary report" }].map(
                ({ icon: Icon, label }) => (
                  <button
                    key={label}
                    className="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-[#F8F9FA] px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition duration-200 hover:border-[#0B3D91]/40 hover:bg-white hover:text-[#0B3D91] hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0B3D91]/30"
                    type="button"
                  >
                    <span className="flex items-center gap-3">
                      <span className="rounded-full bg-[#0B3D91]/10 p-2 text-[#0B3D91]">
                        <Icon className="h-4 w-4" />
                      </span>
                      {label}
                    </span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                ),
              )}
            </div>
          </article>
        </section>
      </div>
    </div>
  );
}
