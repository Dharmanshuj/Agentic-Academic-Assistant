package com.example.demo.controller;

import com.example.demo.dto.EmployeeRegistrationDto;
import com.example.demo.model.Employee;
import com.example.demo.service.EmployeeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/employees")
public class EmployeeController {

    @Autowired
    private EmployeeService employeeService;

    @PostMapping("/register")
    public ResponseEntity<Employee> register(@RequestBody EmployeeRegistrationDto dto) {
        Employee registered = employeeService.registerEmployee(dto);
        return ResponseEntity.ok(registered);
    }
}
