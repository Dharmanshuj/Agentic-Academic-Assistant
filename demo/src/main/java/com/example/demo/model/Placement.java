package com.example.demo.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
@Entity
@Table(name = "placements")
public class Placement {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "placement_id")
    private Integer placementId;

    @Column(name = "student_id")
    private String studentId;

    @Column(name = "company_name")
    private String companyName;

    private String role;

    @Column(name = "package_lpa")
    private BigDecimal packageLpa;

    @Column(name = "placement_status")
    private String placementStatus;

    @Column(name = "placement_date")
    private LocalDate placementDate;
}
