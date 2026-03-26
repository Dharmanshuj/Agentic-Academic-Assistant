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

        // A placeholder hashed password because the Python script checks for $argon2 or
        // updates it
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
}
