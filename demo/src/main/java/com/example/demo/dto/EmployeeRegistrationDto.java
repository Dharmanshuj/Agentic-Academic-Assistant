package com.example.demo.dto;

import lombok.Data;

@Data
public class EmployeeRegistrationDto {
    private String empno;
    private String name;
    private String dept;
    private String designation;
    private String bankName;
    private String accountNo;

    private Double basicSalary;
    private Double hra;
    private Double conveyance;
    private Double medical;
    private Double special;
    private Double grossSalary;

    private Double epf;
    private Double healthInsurance;
    private Double professionalTax;
    private Double tds;
    private Double totalDeductions;
    private Double netPay;

    // Attendance data
    private Integer totalDays;
    private Integer presentDays;
    private Integer absentDays;
    private Integer month;
    private Integer year;
}
