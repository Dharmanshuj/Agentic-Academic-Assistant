package com.example.demo.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "students")
public class Student {

    @Id
    @Column(name = "student_id")
    private String studentId;

    @Column(name = "roll_no")
    private String rollNo;

    @Column(name = "first_name")
    private String firstName;

    @Column(name = "last_name")
    private String lastName;

    private String gender;

    private LocalDate dob;

    private String email;

    private String phone;

    private String department;

    private String program;

    private Integer semester;

    private String section;

    @Column(name = "batch_year")
    private Integer batchYear;

    @Column(name = "admission_year")
    private Integer admissionYear;

    @Column(name = "hostel_name")
    private String hostelName;

    @Column(name = "room_no")
    private String roomNo;

    @Column(name = "guardian_name")
    private String guardianName;

    @Column(name = "guardian_phone")
    private String guardianPhone;

    private String address;

    @Column(name = "hashed_password")
    private String hashedPassword;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}
