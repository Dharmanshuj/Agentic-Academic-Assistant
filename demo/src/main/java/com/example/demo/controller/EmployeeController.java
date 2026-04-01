package com.example.demo.controller;

import com.example.demo.dto.EmployeeRegistrationDto;
import com.example.demo.dto.UpdateAttendanceDto;
import com.example.demo.model.Employee;
import com.example.demo.model.Attendance;
import com.example.demo.service.EmployeeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/employees")
public class EmployeeController {

    @Autowired
    private EmployeeService employeeService;

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody EmployeeRegistrationDto dto) {
        try {
            Employee registered = employeeService.registerEmployee(dto);
            return ResponseEntity.ok(registered);
        } catch (IllegalArgumentException ex) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", ex.getMessage()));
        }
    }

    @PostMapping("/attendance")
    public ResponseEntity<?> updateAttendance(@RequestBody UpdateAttendanceDto dto) {
        try {
            Attendance updated = employeeService.updateAttendance(dto);
            return ResponseEntity.ok(updated);
        } catch (IllegalArgumentException ex) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", ex.getMessage()));
        }
    }
}
