package com.example.demo.service;

import com.example.demo.model.Attendance;
import com.example.demo.model.Employee;
import com.example.demo.model.SalaryPayment;
import com.example.demo.repository.AttendanceRepository;
import com.example.demo.repository.EmployeeRepository;
import com.example.demo.repository.SalaryPaymentRepository;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class PayrollToolService {

    @Autowired
    private EmployeeRepository employeeRepository;

    @Autowired
    private AttendanceRepository attendanceRepository;

    @Autowired
    private SalaryPaymentRepository salaryPaymentRepository;

    // ── Tool 1: get_employee_by_id ──────────────────────────────────────────
    @Tool(description = "Query employee by ID and return profile with salary components, bank details, deductions, and net pay.")
    public Map<String, Object> get_employee_by_id(
            @ToolParam(description = "Employee ID (e.g. 'EMP001')") String empId) {

        @SuppressWarnings("null")
        Optional<Employee> optEmp = employeeRepository.findById(empId);
        if (optEmp.isEmpty()) {
            return Map.of("error", "Employee not found.");
        }

        Employee e = optEmp.get();
        Map<String, Object> record = new LinkedHashMap<>();
        record.put("name", e.getName());
        record.put("department", e.getDept());
        record.put("designation", e.getDesignation());
        record.put("bank_name", e.getBankName());
        record.put("account_no", e.getAccountNo());
        record.put("basic_salary", e.getBasicSalary());
        record.put("hra", e.getHra());
        record.put("conveyance", e.getConveyance());
        record.put("medical", e.getMedical());
        record.put("special", e.getSpecial());
        record.put("gross_salary", e.getGrossSalary());
        record.put("epf", e.getEpf());
        record.put("health_insurance", e.getHealthInsurance());
        record.put("professional_tax", e.getProfessionalTax());
        record.put("tds", e.getTds());
        record.put("total_deductions", e.getTotalDeductions());
        record.put("net_pay", e.getNetPay());
        return record;
    }

    // ── Tool 2: get_attendance ───────────────────────────────────────────────
    @Tool(description = "Get attendance for an employee for a specific month/year. If month and year are not provided, returns the most recent record.")
    public Map<String, Object> get_attendance(
            @ToolParam(description = "Employee ID") String empId,
            @ToolParam(description = "Month (1-12), pass 0 to get the most recent record") int month,
            @ToolParam(description = "Year (e.g. 2026), pass 0 to get the most recent record") int year) {

        Optional<Attendance> optAtt;
        if (month > 0 && year > 0) {
            optAtt = attendanceRepository.findByEmpnoAndMonthAndYear(empId, month, year);
        } else {
            optAtt = attendanceRepository.findFirstByEmpnoOrderByYearDescMonthDesc(empId);
        }

        if (optAtt.isEmpty()) {
            return Map.of("error", "No attendance record found.");
        }

        Attendance a = optAtt.get();
        Map<String, Object> record = new LinkedHashMap<>();
        record.put("attendance_id", a.getId());
        record.put("total_days", a.getTotalDays());
        record.put("present_days", a.getPresentDays());
        record.put("absent_days", a.getAbsentDays());
        record.put("month_recorded", a.getMonth());
        record.put("year_recorded", a.getYear());
        return record;
    }

    // ── Tool 3: get_salary_payment ───────────────────────────────────────────
    @Tool(description = "Fetch final in-hand salary based on attendance ID.")
    public Map<String, Object> get_salary_payment(
            @ToolParam(description = "Attendance record ID") int attendanceId) {

        Optional<SalaryPayment> optSp = salaryPaymentRepository.findByAttendanceId(attendanceId);
        if (optSp.isEmpty()) {
            return Map.of("error", "No salary payment record found.");
        }
        return Map.of("final_salary", optSp.get().getFinalSalary());
    }

    // ── Tool 4: get_all_attendance_for_employee ──────────────────────────────
    @Tool(description = "Get all attendance records for an employee across all months for a specific year.")
    public List<Map<String, Object>> get_all_attendance_for_employee(
            @ToolParam(description = "Employee ID") String empId,
            @ToolParam(description = "Year (e.g. 2026), pass 0 for all years") int year) {

        List<Attendance> records;
        if (year > 0) {
            records = attendanceRepository.findByEmpnoAndYear(empId, year);
        } else {
            records = attendanceRepository.findByEmpno(empId);
        }

        List<Map<String, Object>> result = new ArrayList<>();
        for (Attendance a : records) {
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("attendance_id", a.getId());
            entry.put("total_days", a.getTotalDays());
            entry.put("present_days", a.getPresentDays());
            entry.put("absent_days", a.getAbsentDays());
            entry.put("month", a.getMonth());
            entry.put("year", a.getYear());
            result.add(entry);
        }
        return result;
    }

    // ── Tool 5: get_all_employees_data (ADMIN) ──────────────────────────────
    @Tool(description = "Query data for all employees. Returns empno, name, dept, designation, and net_pay for every employee.")
    public List<Map<String, Object>> get_all_employees_data() {

        List<Employee> employees = employeeRepository.findAll();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Employee e : employees) {
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("empno", e.getEmpno());
            entry.put("name", e.getName());
            entry.put("dept", e.getDept());
            entry.put("designation", e.getDesignation());
            entry.put("net_pay", e.getNetPay());
            result.add(entry);
        }
        return result;
    }

    // ── Tool 6: admin_get_monthly_metrics (ADMIN) ───────────────────────────
    @Tool(description = "Admin tool to get attendance and salary payments for all employees across a given month and year.")
    public List<Map<String, Object>> admin_get_monthly_metrics(
            @ToolParam(description = "Month (1-12), pass 0 for all months") int month,
            @ToolParam(description = "Year (e.g. 2026), pass 0 for default year 2026") int year) {

        int effectiveYear = (year > 0) ? year : 2026;
        List<Employee> employees = employeeRepository.findAll();
        List<Map<String, Object>> result = new ArrayList<>();

        for (Employee e : employees) {
            List<Attendance> attendanceRecords;
            if (month > 0) {
                Optional<Attendance> opt = attendanceRepository.findByEmpnoAndMonthAndYear(
                        e.getEmpno(), month, effectiveYear);
                attendanceRecords = opt.map(List::of).orElse(List.of());
            } else {
                attendanceRecords = attendanceRepository.findByEmpnoAndYear(
                        e.getEmpno(), effectiveYear);
                if (attendanceRecords.isEmpty()) {
                    attendanceRecords = List.of();
                }
            }

            if (attendanceRecords.isEmpty()) {
                // No attendance for this period — include employee with nulls
                Map<String, Object> entry = new LinkedHashMap<>();
                entry.put("empno", e.getEmpno());
                entry.put("name", e.getName());
                entry.put("total_days", null);
                entry.put("present_days", null);
                entry.put("absent_days", null);
                entry.put("inhand_net_pay", null);
                entry.put("month", month > 0 ? month : null);
                entry.put("year", effectiveYear);
                result.add(entry);
            } else {
                for (Attendance a : attendanceRecords) {
                    Optional<SalaryPayment> sp = salaryPaymentRepository.findByAttendanceId(a.getId());
                    Double inhandNetPay = sp.isPresent() ? sp.get().getFinalSalary() : null;
                    Map<String, Object> entry = new LinkedHashMap<>();
                    entry.put("empno", e.getEmpno());
                    entry.put("name", e.getName());
                    entry.put("total_days", a.getTotalDays());
                    entry.put("present_days", a.getPresentDays());
                    entry.put("absent_days", a.getAbsentDays());
                    entry.put("inhand_net_pay", inhandNetPay);
                    entry.put("month", a.getMonth());
                    entry.put("year", a.getYear());
                    result.add(entry);
                }
            }
        }

        return result;
    }
}
