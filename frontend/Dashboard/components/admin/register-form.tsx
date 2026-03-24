"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

export function RegisterEmployeeForm() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const data = Object.fromEntries(formData.entries());

    try {
      const response = await fetch("http://localhost:8080/api/employees/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Basic " + window.btoa("admin:admin"),
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) throw new Error("Failed to register employee");

      toast.success("Employee registered successfully!");
      (e.target as HTMLFormElement).reset();
      router.push("/dashboard");
    } catch (error) {
      toast.error("Registration failed. Please ensure the backend is running.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto mt-10 bg-white dark:bg-zinc-900 border dark:border-zinc-800 rounded-xl shadow-sm overflow-hidden mb-20 text-zinc-900 dark:text-zinc-100">
      <div className="p-6 border-b dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50">
        <h2 className="text-xl font-semibold">Register New Employee</h2>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">Fill in the comprehensive employee details to synchronize with the payroll database.</p>
      </div>
      
      <form onSubmit={handleSubmit} className="p-6 space-y-8">
        {/* Personal & Job Details */}
        <div>
          <h3 className="text-lg font-medium mb-4 border-b border-zinc-200 dark:border-zinc-800 pb-2">Profile Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5"><label className="text-sm font-medium">Employee No.</label><input name="empno" required className="input-field w-full px-3 py-2 text-sm text-black border border-zinc-200 rounded-md bg-transparent" placeholder="EMP123" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Full Name</label><input name="name" required className="input-field w-full px-3 py-2 text-sm text-black border border-zinc-200 rounded-md bg-transparent" placeholder="John Doe" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Department</label><input name="dept" required className="input-field w-full px-3 py-2 text-sm text-black border border-zinc-200 rounded-md bg-transparent" placeholder="Engineering" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Designation</label><input name="designation" required className="input-field w-full px-3 py-2 text-sm text-black border border-zinc-200 rounded-md bg-transparent" placeholder="Software Engineer" /></div>
          </div>
        </div>

        {/* Bank Details */}
        <div>
          <h3 className="text-lg font-medium mb-4 border-b border-zinc-200 dark:border-zinc-800 pb-2">Bank Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5"><label className="text-sm font-medium">Bank Name</label><input name="bankName" required className="input-field w-full text-black px-3 py-2 text-sm border border-zinc-200 rounded-md bg-transparent" placeholder="Chase Bank" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Account No.</label><input name="accountNo" required className="input-field w-full text-black px-3 py-2 text-sm border border-zinc-200 rounded-md bg-transparent" placeholder="1234567890" /></div>
          </div>
        </div>

        {/* Salary Details */}
        <div>
          <h3 className="text-lg font-medium mb-4 border-b border-zinc-200 dark:border-zinc-800 pb-2">Salary & Tax Breakdowns</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-1.5"><label className="text-sm font-medium">Basic Salary</label><input name="basicSalary" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">HRA</label><input name="hra" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Conveyance</label><input name="conveyance" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Medical</label><input name="medical" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Special</label><input name="special" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Gross Salary</label><input name="grossSalary" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">EPF</label><input name="epf" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Health Insur.</label><input name="healthInsurance" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Prof. Tax</label><input name="professionalTax" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">TDS</label><input name="tds" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Total Ded.</label><input name="totalDeductions" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Net Pay</label><input name="netPay" type="number" step="0.01" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="0" /></div>
          </div>
        </div>

        {/* Attendance Details */}
        <div>
          <h3 className="text-lg font-medium mb-4 border-b border-zinc-200 dark:border-zinc-800 pb-2">Initial Attendance Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="space-y-1.5"><label className="text-sm font-medium">Total Days</label><input name="totalDays" type="number" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="30" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Present</label><input name="presentDays" type="number" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="28" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Absent</label><input name="absentDays" type="number" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="2" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Month</label><input name="month" type="number" min="1" max="12" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="10" /></div>
            <div className="space-y-1.5"><label className="text-sm font-medium">Year</label><input name="year" type="number" required className="input-field w-full text-black px-3 py-2 border border-zinc-200 rounded-md bg-transparent" placeholder="2023" /></div>
          </div>
        </div>

        <button 
          type="submit" 
          disabled={loading}
          className="w-full flex items-center justify-center py-3 px-4 mt-6 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-zinc-900 hover:bg-zinc-800 transition-colors"
        >
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Register Employee"}
        </button>
      </form>
    </div>
  );
}
