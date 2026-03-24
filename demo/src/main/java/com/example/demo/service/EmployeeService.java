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
}
