package com.example.demo.config;

import com.example.demo.dto.EmployeeRegistrationDto;
import com.example.demo.dto.McpDtos.*;
import com.example.demo.model.Employee;
import com.example.demo.repository.EmployeeRepository;
import com.example.demo.service.EmployeeService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Description;

import java.util.List;
import java.util.function.Function;

@Configuration
public class McpConfig {

    @Bean
    @Description("Fetch salary summary for an employee by their employee ID (empno)")
    public Function<EmpIdRequest, EmployeeSummary> getEmployeeSummary(EmployeeRepository repository) {
        return request -> repository.findById(request.empno())
            .map(EmployeeSummary::from)
            .orElseThrow(() -> new RuntimeException("Employee not found: " + request.empno()));
    }

    @Bean
    @Description("Get total payroll summary for a specific department")
    public Function<DeptRequest, DeptPayrollSummary> getDepartmentPayroll(EmployeeRepository repository) {
        return request -> {
            List<Employee> employees = repository.findByDept(request.department());
            double totalNetPay = employees.stream()
                .mapToDouble(Employee::getNetPay)
                .sum();
            return new DeptPayrollSummary(request.department(), employees.size(), totalNetPay);
        };
    }

    @Bean
    @Description("Update an employee's basic salary and auto-recalculate their entire payroll structure")
    public Function<UpdateSalaryRequest, EmployeeSummary> updateEmployeeSalary(EmployeeService service) {
        return request -> {
            Employee updated = service.updateEmployeeSalary(request.empno(), request.newBasicSalary());
            return EmployeeSummary.from(updated);
        };
    }

    @Bean
    @Description("Register a new employee into the system via MCP")
    public Function<EmployeeRegistrationDto, EmployeeSummary> registerEmployeeMcp(EmployeeService service) {
        return request -> {
            Employee saved = service.registerEmployee(request);
            return EmployeeSummary.from(saved);
        };
    }
}
