package com.example.demo.repository;

import com.example.demo.model.StudentAttendance;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface StudentAttendanceRepository extends JpaRepository<StudentAttendance, Integer> {

    List<StudentAttendance> findByStudentIdOrderByAttendanceIdDesc(String studentId);

    List<StudentAttendance> findByStudentIdIn(List<String> studentIds);
}
