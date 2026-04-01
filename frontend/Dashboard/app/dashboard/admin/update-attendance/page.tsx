import { UpdateAttendanceForm } from "@/components/admin/update-attendance-form";

export const metadata = {
  title: "Admin | Update Attendance",
};

export default function AdminUpdateAttendancePage() {
  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 bg-zinc-50 dark:bg-zinc-950 w-full overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-white mb-2">Admin Dashboard</h1>
        <p className="text-zinc-500 dark:text-zinc-400 mb-8">Securely update existing employee attendance records for a specific month.</p>
        
        <UpdateAttendanceForm />
      </div>
    </div>
  );
}
