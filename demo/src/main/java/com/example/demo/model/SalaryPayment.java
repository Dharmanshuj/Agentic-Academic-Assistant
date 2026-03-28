package com.example.demo.model;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
public class SalaryPayment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    private String empno;

    private Integer month;
    private Integer year;

    private Integer attendanceId;

    // ---- Computed Fields ----
    private Double grossSalary;
    private Double perDaySalary;
    private Double earnedSalary;

    private Double totalDeductions;
    private Double finalSalary;

    // -------------------------------
    // AUTO CALCULATION (FINAL SALARY)
    // -------------------------------
    @PrePersist
    @PreUpdate
    public void calculateSalary() {

        // NOTE:
        // This assumes fields are already populated
        // from service (Employee + Attendance)

        if (grossSalary == null || perDaySalary == null || earnedSalary == null) return;

        this.finalSalary = earnedSalary - safe(totalDeductions);
    }

    private double safe(Double val) {
        return val != null ? val : 0.0;
    }
}