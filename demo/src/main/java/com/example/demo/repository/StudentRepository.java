package com.example.demo.repository;

import com.example.demo.model.Student;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface StudentRepository extends JpaRepository<Student, String> {

    Optional<Student> findByRollNo(String rollNo);

    Optional<Student> findByRollNoOrStudentId(String rollNo, String studentId);

    List<Student> findAllByOrderByRollNoAsc();

    List<Student> findBySemesterOrderByRollNoAsc(Integer semester);
}
