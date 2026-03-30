package com.example.demo.service;

import com.example.demo.dto.EmployeeRegistrationDto;
import com.example.demo.model.Attendance;
import com.example.demo.model.Employee;
import com.example.demo.model.SalaryPayment;
import com.example.demo.repository.AttendanceRepository;
import com.example.demo.repository.EmployeeRepository;
import com.example.demo.repository.SalaryPaymentRepository;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class EmployeeService {
    private static final java.util.Set<String> ALLOWED_LOCATIONS = java.util.Set.of(
            "gurugram", "bangalore", "delhi", "noida", "pune");

    @Autowired
    private EmployeeRepository employeeRepository;

    @Autowired
    private AttendanceRepository attendanceRepository;

    @Autowired
    private SalaryPaymentRepository salaryPaymentRepository;

    @Transactional
    public Employee registerEmployee(EmployeeRegistrationDto dto) {
        validateRegistration(dto);

        Employee employee = new Employee();
        employee.setEmpno(dto.getEmpno());
        employee.setName(dto.getName());
        employee.setDept(dto.getDept());
        employee.setDesignation(dto.getDesignation());
        employee.setWorkLocation(dto.getWorkLocation());
        employee.setBankName(dto.getBankName());
        employee.setAccountNo(dto.getAccountNo());
        employee.setBasicSalary(dto.getBasicSalary());
        employee.setIsMetro(false);
        employee.setConveyance(dto.getConveyance());
        employee.setMedical(dto.getMedical());
        employee.setSpecial(dto.getSpecial());
        employee.setHealthInsurance(dto.getHealthInsurance());
        employee.setTds(dto.getTds());

        employee.setHashedPassword("CHANGEME");

        Employee savedEmployee = employeeRepository.save(employee);

        Attendance attendance = new Attendance();
        attendance.setEmpno(dto.getEmpno());
        attendance.setTotalDays(dto.getTotalDays());
        attendance.setPresentDays(dto.getPresentDays());
        attendance.setAbsentDays(resolveAbsentDays(dto));
        attendance.setMonth(dto.getMonth());
        attendance.setYear(dto.getYear());
        Attendance savedAttendance = attendanceRepository.save(attendance);

        SalaryPayment salaryPayment = buildSalaryPayment(savedEmployee, savedAttendance);
        if (salaryPayment == null)
            throw new RuntimeException("salaryPayment is null");
        salaryPaymentRepository.save(salaryPayment);

        return savedEmployee;
    }

    @SuppressWarnings("null")
    private void validateRegistration(EmployeeRegistrationDto dto) {
        if (dto.getEmpno() == null || dto.getEmpno().isBlank()) {
            throw new IllegalArgumentException("Employee number is required.");
        }
        if (dto.getName() == null || dto.getName().isBlank()) {
            throw new IllegalArgumentException("Employee name is required.");
        }
        if (dto.getDept() == null || dto.getDept().isBlank()) {
            throw new IllegalArgumentException("Department is required.");
        }
        if (dto.getDesignation() == null || dto.getDesignation().isBlank()) {
            throw new IllegalArgumentException("Designation is required.");
        }
        if (dto.getWorkLocation() == null || dto.getWorkLocation().isBlank()) {
            throw new IllegalArgumentException("Work location is required.");
        }
        if (!ALLOWED_LOCATIONS.contains(dto.getWorkLocation().trim().toLowerCase(java.util.Locale.ROOT))) {
            throw new IllegalArgumentException(
                    "Work location must be one of Gurugram, Bangalore, Delhi, Noida, or Pune.");
        }
        if (dto.getBankName() == null || dto.getBankName().isBlank()) {
            throw new IllegalArgumentException("Bank name is required.");
        }
        if (dto.getAccountNo() == null || dto.getAccountNo().isBlank()) {
            throw new IllegalArgumentException("Account number is required.");
        }
        if (dto.getBasicSalary() == null || dto.getBasicSalary() <= 0) {
            throw new IllegalArgumentException("Basic salary must be greater than zero.");
        }
        if (dto.getTotalDays() == null || dto.getTotalDays() <= 0) {
            throw new IllegalArgumentException("Total days must be greater than zero.");
        }
        if (dto.getPresentDays() == null || dto.getPresentDays() < 0) {
            throw new IllegalArgumentException("Present days must be zero or more.");
        }
        if (dto.getPresentDays() > dto.getTotalDays()) {
            throw new IllegalArgumentException("Present days cannot exceed total days.");
        }
        if (dto.getMonth() == null || dto.getMonth() < 1 || dto.getMonth() > 12) {
            throw new IllegalArgumentException("Month must be between 1 and 12.");
        }
        if (dto.getYear() == null || dto.getYear() < 2000) {
            throw new IllegalArgumentException("Year must be valid.");
        }
        if (employeeRepository.existsById(dto.getEmpno())) {
            throw new IllegalArgumentException("Employee already exists.");
        }
    }

    private Integer resolveAbsentDays(EmployeeRegistrationDto dto) {
        if (dto.getAbsentDays() != null) {
            int expectedAbsentDays = dto.getTotalDays() - dto.getPresentDays();
            if (!dto.getAbsentDays().equals(expectedAbsentDays)) {
                throw new IllegalArgumentException("Absent days must equal total days minus present days.");
            }
            return dto.getAbsentDays();
        }

        return dto.getTotalDays() - dto.getPresentDays();
    }

    private SalaryPayment buildSalaryPayment(Employee employee, Attendance attendance) {
        SalaryPayment salaryPayment = new SalaryPayment();
        salaryPayment.setEmpno(employee.getEmpno());
        salaryPayment.setMonth(attendance.getMonth());
        salaryPayment.setYear(attendance.getYear());
        salaryPayment.setAttendanceId(attendance.getId());
        salaryPayment.setGrossSalary(employee.getGrossSalary());

        double perDaySalary = employee.getGrossSalary() / attendance.getTotalDays();
        double earnedSalary = perDaySalary * attendance.getPresentDays();

        salaryPayment.setPerDaySalary(perDaySalary);
        salaryPayment.setEarnedSalary(earnedSalary);
        salaryPayment.setTotalDeductions(employee.getTotalDeductions());
        salaryPayment.setFinalSalary(earnedSalary - employee.getTotalDeductions());
        return salaryPayment;
    }
}
