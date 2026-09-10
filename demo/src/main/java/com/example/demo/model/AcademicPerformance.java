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
@Table(name = "academic_performance")
public class AcademicPerformance {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "result_id")
    private Integer resultId;

    @Column(name = "student_id")
    private String studentId;

    private Integer semester;

    private BigDecimal sgpa;

    private BigDecimal cgpa;

    private Integer backlogs;

    @Column(name = "academic_year")
    private String academicYear;
}
