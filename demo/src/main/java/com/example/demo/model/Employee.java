package com.example.demo.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import lombok.Data;

import java.util.Locale;

@Data
@Entity
public class Employee {
    @Id
    private String empno;

    private String name;
    private String dept;
    private String designation;
    private String workLocation;

    private String bankName;
    private String accountNo;

    // ---- Core Salary ----
    private Double basicSalary;
    private Boolean isMetro;

    // ---- Calculated Components ----
    private Double hra;
    private Double conveyance;
    private Double medical;
    private Double special;

    private Double grossSalary;

    // ---- Deductions ----
    private Double epf;
    private Double healthInsurance;
    private Double professionalTax;
    private Double tds;

    private Double totalDeductions;
    private Double netPay;

    private String hashedPassword;

    // -------------------------------
    // AUTO CALCULATION (CTC LEVEL)
    // -------------------------------
    @PrePersist
    @PreUpdate
    public void calculateCTC() {

        if (basicSalary == null)
            return;

        double basic = basicSalary;

        // HRA is 50% for metro cities, 40% for non-metro
        this.hra = (this.isMetro != null && this.isMetro) ? 0.5 * basic : 0.4 * basic;

        // EPF
        this.epf = 0.12 * basic;

        // Allowances
        this.conveyance = (conveyance == null || conveyance <= 0) ? 0.05 * basic : conveyance;
        this.medical = (medical == null || medical <= 0) ? 0.05 * basic : medical;

        // Special (balancing or fixed %)
        this.special = (special == null || special <= 0) ? 0.1 * basic : special;

        // Gross
        this.grossSalary = basic + hra + conveyance + medical + special;

        // Deductions
        double insurance = safe(healthInsurance);
        double pt = calculateProfessionalTax(workLocation);
        double tax = safe(tds);

        this.professionalTax = pt;
        this.totalDeductions = epf + insurance + pt + tax;

        // Net (without attendance impact)
        this.netPay = grossSalary - totalDeductions;
    }

    private double safe(Double val) {
        return val != null ? val : 0.0;
    }

    private double calculateProfessionalTax(String location) {
        if (location == null) {
            return 0.0;
        }

        return switch (location.trim().toLowerCase(Locale.ROOT)) {
            case "gurugram" -> 0.0;
            case "delhi" -> 200.0;
            case "noida" -> 150.0;
            case "bangalore" -> 250.0;
            case "pune" -> 200.0;
            default -> 0.0;
        };
    }
}
