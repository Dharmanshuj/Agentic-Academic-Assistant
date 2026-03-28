package com.example.demo.repository;

import com.example.demo.model.Attendance;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface AttendanceRepository extends JpaRepository<Attendance, Long> {
    Optional<Attendance> findByEmpnoAndMonthAndYear(String empno, Integer month, Integer year);
    List<Attendance> findByMonthAndYear(Integer month, Integer year);
    List<Attendance> findByEmpno(String empno);
    List<Attendance> findByEmpnoAndYear(String empno, Integer year);
    Optional<Attendance> findFirstByEmpnoOrderByYearDescMonthDesc(String empno);
}
