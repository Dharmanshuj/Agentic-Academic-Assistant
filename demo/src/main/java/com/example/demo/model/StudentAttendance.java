package com.example.demo.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;

import java.math.BigDecimal;

@Data
@Entity
@Table(name = "attendance")
public class StudentAttendance {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "attendance_id")
    private Integer attendanceId;

    @Column(name = "student_id")
    private String studentId;

    @Column(name = "subject_id")
    private String subjectId;

    @Column(name = "total_classes")
    private Integer totalClasses;

    @Column(name = "attended_classes")
    private Integer attendedClasses;

    @Column(name = "attendance_percentage")
    private BigDecimal attendancePercentage;
}
