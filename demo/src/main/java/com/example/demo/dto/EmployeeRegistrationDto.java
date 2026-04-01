package com.example.demo.dto;

import lombok.Data;

@Data
public class EmployeeRegistrationDto {
    private String empno;
    private String name;
    private String dept;
    private String designation;
    private String workLocation;
    private String bankName;
    private String accountNo;

    private Double basicSalary;
    private Double conveyance;
    private Double medical;
    private Double special;
    private Double healthInsurance;
    private Double tds;

}
