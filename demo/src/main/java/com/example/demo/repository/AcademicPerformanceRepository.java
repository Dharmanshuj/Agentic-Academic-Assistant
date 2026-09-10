package com.example.demo.repository;

import com.example.demo.model.AcademicPerformance;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface AcademicPerformanceRepository extends JpaRepository<AcademicPerformance, Integer> {

    Optional<AcademicPerformance> findFirstByStudentIdAndSemesterOrderByResultIdDesc(String studentId, Integer semester);

    Optional<AcademicPerformance> findFirstByStudentIdAndSemesterAndAcademicYearContainingOrderByResultIdDesc(
            String studentId,
            Integer semester,
            String academicYear
    );

    List<AcademicPerformance> findBySemesterOrderByStudentIdAsc(Integer semester);

    List<AcademicPerformance> findByStudentIdIn(List<String> studentIds);

    boolean existsByStudentIdAndAcademicYearContaining(String studentId, String academicYear);
}
