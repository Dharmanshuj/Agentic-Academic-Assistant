package com.example.demo.service.mcp;
import org.springframework.ai.mcp.annotation.McpTool;
import org.springframework.ai.mcp.annotation.McpToolParam;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import java.util.*;

@Service
public class PayrollMcpService {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    // --- SECURITY STUBS (Replaces your Python security imports) ---
    private Map<String, Object> applySecurity(Map<String, Object> record) {
        // Implement your masking/filtering logic here
        // e.g., record.put("account_no", "****" + lastFourDigits);
        return record;
    }

    @McpTool(name = "get_all_employees_data", 
             description = "Fetch directory of ALL employees. Use for company-wide overview.")
    public List<Map<String, Object>> getAllEmployeesData() {
        String sql = "SELECT empno, name, dept, designation, net_pay FROM employees";
        return jdbcTemplate.queryForList(sql);
    }

    @McpTool(name = "admin_get_monthly_metrics", 
             description = "Get attendance and salary data for ALL employees for a specific month/year.")
    public List<Map<String, Object>> adminGetMonthlyMetrics(
            @McpToolParam(description = "Month 1-12") Integer month,
            @McpToolParam(description = "Year e.g. 2026") Integer year) {
        
        String sql;
        Object[] params;

        if (month != null && year != null) {
            sql = "SELECT e.empno, e.name, a.total_days, a.present_days, a.absent_days, s.inhand_net_pay, a.month, a.year " +
                  "FROM employees e LEFT JOIN attendance a ON e.empno = a.empno AND a.month = ? AND a.year = ? " +
                  "LEFT JOIN salary_payments s ON a.id = s.attendance_id";
            params = new Object[]{month, year};
        } else if (year != null) {
            sql = "SELECT e.empno, e.name, a.total_days, a.present_days, a.absent_days, s.inhand_net_pay, a.month, a.year " +
                  "FROM employees e LEFT JOIN attendance a ON e.empno = a.empno AND a.year = ? " +
                  "LEFT JOIN salary_payments s ON a.id = s.attendance_id";
            params = new Object[]{year};
        } else {
            sql = "SELECT e.empno, e.name, a.total_days, a.present_days, a.absent_days, s.inhand_net_pay, a.month, a.year " +
                  "FROM employees e LEFT JOIN attendance a ON e.empno = a.empno AND a.year = 2026 " +
                  "LEFT JOIN salary_payments s ON a.id = s.attendance_id";
            params = new Object[]{};
        }
        return jdbcTemplate.queryForList(sql, params);
    }

    @McpTool(name = "get_employee_by_id", 
             description = "Fetch complete salary structure for a single employee by ID.")
    public Map<String, Object> getEmployeeById(@McpToolParam(description = "Employee ID") String empId) {
        String sql = "SELECT * FROM employees WHERE empno = ?";
        try {
            Map<String, Object> record = jdbcTemplate.queryForMap(sql, empId);
            return applySecurity(record);
        } catch (Exception e) {
            return Map.of("error", "Employee not found.");
        }
    }

    @McpTool(name = "get_attendance", 
             description = "Fetch attendance data. Call this BEFORE get_salary_payment.")
    public Map<String, Object> getAttendance(
            @McpToolParam(description = "Employee ID") String empId,
            @McpToolParam(description = "Month 1-12") Integer month,
            @McpToolParam(description = "Year") Integer year) {
        
        String sql;
        Object[] params;

        if (month != null && year != null) {
            sql = "SELECT id, total_days, present_days, absent_days, month, year FROM attendance " +
                  "WHERE empno = ? AND month = ? AND year = ?";
            params = new Object[]{empId, month, year};
        } else {
            sql = "SELECT id, total_days, present_days, absent_days, month, year FROM attendance " +
                  "WHERE empno = ? ORDER BY year DESC, month DESC LIMIT 1";
            params = new Object[]{empId};
        }

        try {
            return jdbcTemplate.queryForMap(sql, params);
        } catch (Exception e) {
            return Map.of("error", "No attendance record found.");
        }
    }

    @McpTool(name = "get_salary_payment", 
             description = "Fetch finalized in-hand salary. Requires attendance_id.")
    public Map<String, Object> getSalaryPayment(@McpToolParam(description = "ID from get_attendance") int attendanceId) {
        String sql = "SELECT inhand_net_pay FROM salary_payments WHERE attendance_id = ?";
        try {
            Double amount = jdbcTemplate.queryForObject(sql, Double.class, attendanceId);
            return Map.of("final_salary", amount);
        } catch (Exception e) {
            return Map.of("error", "No payment record found.");
        }
    }

    @McpTool(name = "get_all_attendance_for_employee", 
             description = "Fetch ALL monthly attendance records for a single employee across the year.")
    public List<Map<String, Object>> getAllAttendanceForEmployee(
            @McpToolParam(description = "Employee ID") String empId,
            @McpToolParam(description = "Year") Integer year) {
        
        String sql;
        Object[] params;

        if (year != null) {
            sql = "SELECT id as attendance_id, total_days, present_days, absent_days, month, year FROM attendance " +
                  "WHERE empno = ? AND year = ? ORDER BY year DESC, month DESC";
            params = new Object[]{empId, year};
        } else {
            sql = "SELECT id as attendance_id, total_days, present_days, absent_days, month, year FROM attendance " +
                  "WHERE empno = ? ORDER BY year DESC, month DESC";
            params = new Object[]{empId};
        }
        return jdbcTemplate.queryForList(sql, params);
    }
}