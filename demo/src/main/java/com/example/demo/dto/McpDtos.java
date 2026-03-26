package com.example.demo.dto;

import com.example.demo.model.Employee;

public class McpDtos {

    public record EmpIdRequest(String empno) {}

    public record DeptRequest(String department) {}

    public record UpdateSalaryRequest(String empno, Double newBasicSalary) {}

    public record EmployeeSummary(
        String empno,
        String name,
        String dept,
        String designation,
        Double basicSalary,
        Double netPay
    ) {
        public static EmployeeSummary from(Employee e) {
            return new EmployeeSummary(
                e.getEmpno(),
                e.getName(),
                e.getDept(),
                e.getDesignation(),
                e.getBasicSalary(),
                e.getNetPay()
            );
        }
    }

    public record DeptPayrollSummary(String dept, int headCount, Double totalNetPay) {}
}
