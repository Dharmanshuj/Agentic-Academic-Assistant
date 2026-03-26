package com.example.demo.service;

import com.example.demo.dto.EmployeeRegistrationDto;
import com.example.demo.model.Attendance;
import com.example.demo.model.Employee;
import com.example.demo.repository.AttendanceRepository;
import com.example.demo.repository.EmployeeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class EmployeeService {

    @Autowired
    private EmployeeRepository employeeRepository;

    @Autowired
    private AttendanceRepository attendanceRepository;

    @Transactional
    public Employee registerEmployee(EmployeeRegistrationDto dto) {
        Employee employee = new Employee();
        employee.setEmpno(dto.getEmpno());
        employee.setName(dto.getName());
        employee.setDept(dto.getDept());
        employee.setDesignation(dto.getDesignation());
        employee.setBankName(dto.getBankName());
        employee.setAccountNo(dto.getAccountNo());
        // Calculate Gross Salary
        double basic = dto.getBasicSalary() != null ? dto.getBasicSalary() : 0.0;
        double hra = dto.getHra() != null ? dto.getHra() : 0.0;
        double conveyance = dto.getConveyance() != null ? dto.getConveyance() : 0.0;
        double medical = dto.getMedical() != null ? dto.getMedical() : 0.0;
        double special = dto.getSpecial() != null ? dto.getSpecial() : 0.0;
        double grossSalary = basic + hra + conveyance + medical + special;

        // Calculate Total Deductions
        double epf = dto.getEpf() != null ? dto.getEpf() : 0.0;
        double healthInsurance = dto.getHealthInsurance() != null ? dto.getHealthInsurance() : 0.0;
        double professionalTax = dto.getProfessionalTax() != null ? dto.getProfessionalTax() : 0.0;
        double tds = dto.getTds() != null ? dto.getTds() : 0.0;
        double totalDeductions = epf + healthInsurance + professionalTax + tds;

        // Calculate Net Pay
        double netPay = grossSalary - totalDeductions;

        employee.setBasicSalary(basic);
        employee.setHra(hra);
        employee.setConveyance(conveyance);
        employee.setMedical(medical);
        employee.setSpecial(special);
        employee.setGrossSalary(grossSalary);
        employee.setEpf(epf);
        employee.setHealthInsurance(healthInsurance);
        employee.setProfessionalTax(professionalTax);
        employee.setTds(tds);
        employee.setTotalDeductions(totalDeductions);
        employee.setNetPay(netPay);
        
        // A placeholder hashed password because the Python script checks for $argon2 or updates it
        employee.setHashedPassword("CHANGEME");

        Employee savedEmployee = employeeRepository.save(employee);

        Attendance attendance = new Attendance();
        attendance.setEmpno(dto.getEmpno());
        attendance.setTotalDays(dto.getTotalDays());
        attendance.setPresentDays(dto.getPresentDays());
        attendance.setAbsentDays(dto.getAbsentDays());
        attendance.setMonth(dto.getMonth());
        attendance.setYear(dto.getYear());
        attendanceRepository.save(attendance);

        return savedEmployee;
    }

    @Transactional
    public Employee updateEmployeeSalary(String empno, Double newBasicSalary) {
        Employee employee = employeeRepository.findById(empno)
            .orElseThrow(() -> new RuntimeException("Employee not found"));
        
        employee.setBasicSalary(newBasicSalary);
        
        // Recalculate salary logic (Simplified for now, using the same ratios as before)
        // basic: 50k, hra: 20k, conveyance: 3k, medical: 2k, special: 5k = 80k gross
        // epf: 12% of basic (6k), health: 2k, pt: 200, tds: 10% of basic (5k) = 13.2k deductions
        // net: 66.8k
        
        double basic = newBasicSalary;
        employee.setHra(basic * 0.4);
        employee.setConveyance(basic * 0.06);
        employee.setMedical(basic * 0.04);
        employee.setSpecial(basic * 0.1);
        
        double gross = basic + employee.getHra() + employee.getConveyance() + employee.getMedical() + employee.getSpecial();
        employee.setGrossSalary(gross);
        
        employee.setEpf(basic * 0.12);
        employee.setHealthInsurance(2000.0);
        employee.setProfessionalTax(200.0);
        employee.setTds(basic * 0.1);
        
        double deductions = employee.getEpf() + employee.getHealthInsurance() + employee.getProfessionalTax() + employee.getTds();
        employee.setTotalDeductions(deductions);
        employee.setNetPay(gross - deductions);
        
        return employeeRepository.save(employee);
    }
}
