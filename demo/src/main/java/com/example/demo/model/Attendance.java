package com.example.demo.model;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
@Table(name = "attendance")
public class Attendance {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String empno;
    
    @Column(name = "total_days")
    private Integer totalDays;
    
    @Column(name = "present_days")
    private Integer presentDays;
    
    @Column(name = "absent_days")
    private Integer absentDays;
    
    private Integer month;
    private Integer year;
}
