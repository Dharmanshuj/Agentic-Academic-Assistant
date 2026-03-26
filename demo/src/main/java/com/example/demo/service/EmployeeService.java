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
        employee.setBasicSalary(dto.getBasicSalary());
        employee.setHra(dto.getHra());
        employee.setConveyance(dto.getConveyance());
        employee.setMedical(dto.getMedical());
        employee.setSpecial(dto.getSpecial());
        employee.setGrossSalary(dto.getGrossSalary());
        employee.setEpf(dto.getEpf());
        employee.setHealthInsurance(dto.getHealthInsurance());
        employee.setProfessionalTax(dto.getProfessionalTax());
        employee.setTds(dto.getTds());
        employee.setTotalDeductions(dto.getTotalDeductions());
        employee.setNetPay(dto.getNetPay());
        
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
