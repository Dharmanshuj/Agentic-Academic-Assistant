package com.example.demo.service;

import com.example.demo.dto.UpdateAttendanceDto;
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
        String loc = dto.getWorkLocation() != null ? dto.getWorkLocation().trim().toLowerCase(java.util.Locale.ROOT)
                : "";
        boolean metro = loc.equals("delhi") || loc.equals("mumbai") || loc.equals("chennai") || loc.equals("kolkata");
        employee.setIsMetro(metro);
        employee.setConveyance(dto.getConveyance());
        employee.setMedical(dto.getMedical());
        employee.setSpecial(dto.getSpecial());
        employee.setHealthInsurance(dto.getHealthInsurance());
        employee.setTds(dto.getTds());

        employee.setHashedPassword("CHANGEME");

        Employee savedEmployee = employeeRepository.save(employee);

        return savedEmployee;
    }

    @Transactional
    public Attendance updateAttendance(UpdateAttendanceDto dto) {
        if (dto.getEmpno() == null || dto.getEmpno().isBlank()) {
            throw new IllegalArgumentException("Employee number is required.");
        }
        if (dto.getMonth() == null || dto.getYear() == null) {
            throw new IllegalArgumentException("Month and year are required.");
        }

        String empNo = dto.getEmpno();
        if (empNo == null) {
            throw new IllegalArgumentException("Employee ID cannot be null");
        }

        Employee employee = employeeRepository.findById(empNo)
                .orElseThrow(() -> new IllegalArgumentException("Employee not found with id: " + empNo));

        Attendance attendance = attendanceRepository
                .findByEmpnoAndMonthAndYear(dto.getEmpno(), dto.getMonth(), dto.getYear())
                .orElseGet(Attendance::new);

        attendance.setEmpno(dto.getEmpno());
        attendance.setMonth(dto.getMonth());
        attendance.setYear(dto.getYear());
        attendance.setTotalDays(dto.getTotalDays());
        attendance.setPresentDays(dto.getPresentDays());

        Integer absentDays = dto.getAbsentDays();
        if (absentDays == null) {
            absentDays = dto.getTotalDays() - dto.getPresentDays();
        }
        attendance.setAbsentDays(absentDays);

        Attendance savedAttendance = attendanceRepository.save(attendance);

        // Update or create corresponding SalaryPayment
        // 1. Try to find existing, or build a new one if not found
        SalaryPayment salaryPayment = salaryPaymentRepository
                .findByAttendanceId(savedAttendance.getId())
                .orElseGet(() -> buildSalaryPayment(employee, savedAttendance));

        // 2. If it wasn't a new one (it was found), update the calculations
        if (salaryPayment.getId() != null) {
            double perDaySalary = employee.getGrossSalary() / savedAttendance.getTotalDays();
            double earnedSalary = perDaySalary * savedAttendance.getPresentDays();

            salaryPayment.setPerDaySalary(perDaySalary);
            salaryPayment.setEarnedSalary(earnedSalary);
            salaryPayment.setFinalSalary(earnedSalary - employee.getTotalDeductions());
        }

        // 3. Now 'salaryPayment' is guaranteed to be @NonNull
        salaryPaymentRepository.save(salaryPayment);

        return savedAttendance;
    }

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
        if (employeeRepository.existsById(dto.getEmpno())) {
            throw new IllegalArgumentException("Employee already exists.");
        }
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
