package com.example.demo.model;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
public class Attendance {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    private String empno;

    private Integer month;
    private Integer year;

    private Integer totalDays;
    private Integer presentDays;
    private Integer absentDays;
}