package com.example.demo.repository;

import com.example.demo.model.Placement;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PlacementRepository extends JpaRepository<Placement, Integer> {

    List<Placement> findByStudentIdIn(List<String> studentIds);
}
