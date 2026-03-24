package com.example.demo.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;

@Data
@Entity
@Table(name = "employees")
public class Employee {

    @Id
    private String empno;

    private String name;
    private String dept;
    private String designation;
    
    @Column(name = "bank_name")
    private String bankName;
    
    @Column(name = "account_no")
    private String accountNo;

    @Column(name = "basic_salary")
    private Double basicSalary;
    
    private Double hra;
    private Double conveyance;
    private Double medical;
    private Double special;
    
    @Column(name = "gross_salary")
    private Double grossSalary;

    private Double epf;
    
    @Column(name = "health_insurance")
    private Double healthInsurance;
    
    @Column(name = "professional_tax")
    private Double professionalTax;
    
    private Double tds;
    
    @Column(name = "total_deductions")
    private Double totalDeductions;
    
    @Column(name = "net_pay")
    private Double netPay;

    @Column(name = "hashed_password")
    private String hashedPassword;
}
