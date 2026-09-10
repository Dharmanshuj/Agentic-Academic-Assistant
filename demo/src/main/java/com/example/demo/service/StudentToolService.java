package com.example.demo.service;

import com.example.demo.model.AcademicPerformance;
import com.example.demo.model.Internship;
import com.example.demo.model.Placement;
import com.example.demo.model.Student;
import com.example.demo.model.StudentAttendance;
import com.example.demo.model.Subject;
import com.example.demo.repository.AcademicPerformanceRepository;
import com.example.demo.repository.InternshipRepository;
import com.example.demo.repository.PlacementRepository;
import com.example.demo.repository.StudentAttendanceRepository;
import com.example.demo.repository.StudentRepository;
import com.example.demo.repository.SubjectRepository;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class StudentToolService {

    private final StudentRepository studentRepository;
    private final AcademicPerformanceRepository academicPerformanceRepository;
    private final StudentAttendanceRepository studentAttendanceRepository;
    private final SubjectRepository subjectRepository;
    private final PlacementRepository placementRepository;
    private final InternshipRepository internshipRepository;

    public StudentToolService(
            StudentRepository studentRepository,
            AcademicPerformanceRepository academicPerformanceRepository,
            StudentAttendanceRepository studentAttendanceRepository,
            SubjectRepository subjectRepository,
            PlacementRepository placementRepository,
            InternshipRepository internshipRepository
    ) {
        this.studentRepository = studentRepository;
        this.academicPerformanceRepository = academicPerformanceRepository;
        this.studentAttendanceRepository = studentAttendanceRepository;
        this.subjectRepository = subjectRepository;
        this.placementRepository = placementRepository;
        this.internshipRepository = internshipRepository;
    }

    @Tool(description = "Query student profile by roll number or student ID.")
    public Map<String, Object> get_student_by_id(
            @ToolParam(description = "Student roll number or student ID") String studentId) {

        Optional<Student> maybeStudent = studentRepository.findByRollNoOrStudentId(studentId, studentId);
        if (maybeStudent.isEmpty()) {
            return Map.of("error", "Student not found.");
        }

        Student student = maybeStudent.get();
        Optional<AcademicPerformance> maybePerf = academicPerformanceRepository
                .findFirstByStudentIdAndSemesterOrderByResultIdDesc(student.getStudentId(), student.getSemester());

        Map<String, Object> record = new LinkedHashMap<>();
        record.put("student_id", student.getStudentId());
        record.put("roll_no", student.getRollNo());
        record.put("name", buildName(student));
        record.put("department", student.getDepartment());
        record.put("program", student.getProgram());
        record.put("semester", student.getSemester());
        record.put("section", student.getSection());
        record.put("batch_year", student.getBatchYear());
        record.put("admission_year", student.getAdmissionYear());
        record.put("hostel_name", student.getHostelName());
        record.put("room_no", student.getRoomNo());
        record.put("email", student.getEmail());
        record.put("phone", student.getPhone());

        if (maybePerf.isPresent()) {
            AcademicPerformance ap = maybePerf.get();
            record.put("sgpa", ap.getSgpa());
            record.put("cgpa", ap.getCgpa());
            record.put("backlogs", ap.getBacklogs());
            record.put("academic_year", ap.getAcademicYear());
        } else {
            record.put("sgpa", null);
            record.put("cgpa", null);
            record.put("backlogs", null);
            record.put("academic_year", null);
        }

        return record;
    }

    @Tool(description = "Get attendance for a student. If month/year are 0, returns overall aggregated attendance.")
    public Map<String, Object> get_attendance(
            @ToolParam(description = "Student roll number or student ID") String studentId,
            @ToolParam(description = "Month (1-12), pass 0 for aggregate") int month,
            @ToolParam(description = "Year (e.g. 2026), pass 0 for aggregate") int year) {

        Optional<Student> maybeStudent = studentRepository.findByRollNoOrStudentId(studentId, studentId);
        if (maybeStudent.isEmpty()) {
            return Map.of("error", "Student not found.");
        }

        Student student = maybeStudent.get();

        // Month is accepted for API compatibility, but not filterable with current schema.
        if (month > 0) {
            // no-op
        }

        if (year > 0 && !academicPerformanceRepository.existsByStudentIdAndAcademicYearContaining(
                student.getStudentId(),
                String.valueOf(year)
        )) {
            return Map.of("error", "No attendance record found.");
        }

        List<StudentAttendance> records = studentAttendanceRepository.findByStudentIdOrderByAttendanceIdDesc(student.getStudentId());
        if (records.isEmpty()) {
            return Map.of("error", "No attendance record found.");
        }

        int totalClasses = records.stream().mapToInt(r -> safeInt(r.getTotalClasses())).sum();
        int attendedClasses = records.stream().mapToInt(r -> safeInt(r.getAttendedClasses())).sum();
        BigDecimal percentage = BigDecimal.valueOf(totalClasses > 0 ? (attendedClasses * 100.0) / totalClasses : 0.0)
                .setScale(2, RoundingMode.HALF_UP);

        Integer minAttendanceId = records.stream()
                .map(StudentAttendance::getAttendanceId)
                .filter(id -> id != null)
                .min(Integer::compareTo)
                .orElse(null);

        Map<String, Object> record = new LinkedHashMap<>();
        record.put("attendance_id", minAttendanceId);
        record.put("total_classes", totalClasses);
        record.put("attended_classes", attendedClasses);
        record.put("attendance_percentage", percentage);

        // Compatibility aliases expected by the existing Python layer
        record.put("total_days", totalClasses);
        record.put("present_days", attendedClasses);
        record.put("absent_days", Math.max(totalClasses - attendedClasses, 0));

        return record;
    }

    @SuppressWarnings("null")
    @Tool(description = "Get semester results for all students in a specific semester.")
    public List<Map<String, Object>> get_semester_results(
            @ToolParam(description = "Semester number") int semester) {

        List<AcademicPerformance> performances = academicPerformanceRepository.findBySemesterOrderByStudentIdAsc(semester);
        if (performances.isEmpty()) {
            return List.of();
        }

        Set<String> studentIds = performances.stream().map(AcademicPerformance::getStudentId).collect(Collectors.toSet());
        Map<String, Student> studentsById = new LinkedHashMap<>();
        for (String id : studentIds) {
            studentRepository.findById(id).ifPresent(student -> studentsById.put(id, student));
        }

        return performances.stream().map(ap -> {
            Student s = studentsById.get(ap.getStudentId());
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("student_id", ap.getStudentId());
            row.put("roll_no", s != null ? s.getRollNo() : null);
            row.put("name", s != null ? buildName(s) : null);
            row.put("semester", ap.getSemester());
            row.put("sgpa", ap.getSgpa());
            row.put("cgpa", ap.getCgpa());
            row.put("backlogs", ap.getBacklogs());
            row.put("academic_year", ap.getAcademicYear());
            return row;
        }).toList();
    }

    @SuppressWarnings("null")
    @Tool(description = "Get all attendance records for a student. Year is optional; pass 0 for all records.")
    public List<Map<String, Object>> get_all_attendance_for_student(
            @ToolParam(description = "Student roll number or student ID") String studentId,
            @ToolParam(description = "Year (e.g. 2026), pass 0 for all") int year) {

        Optional<Student> maybeStudent = studentRepository.findByRollNoOrStudentId(studentId, studentId);
        if (maybeStudent.isEmpty()) {
            return List.of();
        }

        Student student = maybeStudent.get();

        if (year > 0 && !academicPerformanceRepository.existsByStudentIdAndAcademicYearContaining(
                student.getStudentId(),
                String.valueOf(year)
        )) {
            return List.of();
        }

        List<StudentAttendance> records = studentAttendanceRepository.findByStudentIdOrderByAttendanceIdDesc(student.getStudentId());
        if (records.isEmpty()) {
            return List.of();
        }

        Set<String> subjectIds = records.stream()
                .map(StudentAttendance::getSubjectId)
                .filter(s -> s != null && !s.isBlank())
                .collect(Collectors.toSet());

        Map<String, Subject> subjectById = new LinkedHashMap<>();
        for (String id : subjectIds) {
            subjectRepository.findById(id).ifPresent(subject -> subjectById.put(id, subject));
        }

        return records.stream().map(a -> {
            Subject sub = a.getSubjectId() != null ? subjectById.get(a.getSubjectId()) : null;
            int totalDays = safeInt(a.getTotalClasses());
            int presentDays = safeInt(a.getAttendedClasses());

            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("attendance_id", a.getAttendanceId());
            entry.put("subject_id", a.getSubjectId());
            entry.put("subject_code", sub != null ? sub.getSubjectCode() : null);
            entry.put("subject_name", sub != null ? sub.getSubjectName() : null);
            entry.put("total_classes", a.getTotalClasses());
            entry.put("attended_classes", a.getAttendedClasses());
            entry.put("attendance_percentage", a.getAttendancePercentage());
            entry.put("total_days", totalDays);
            entry.put("present_days", presentDays);
            entry.put("absent_days", Math.max(totalDays - presentDays, 0));
            return entry;
        }).toList();
    }

    @Tool(description = "Get basic data for all students.")
    public List<Map<String, Object>> get_all_students_data() {
        List<Student> students = studentRepository.findAllByOrderByRollNoAsc();

        return students.stream().map(s -> {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("student_id", s.getStudentId());
            row.put("roll_no", s.getRollNo());
            row.put("name", buildName(s));
            row.put("department", s.getDepartment());
            row.put("program", s.getProgram());
            row.put("semester", s.getSemester());
            row.put("section", s.getSection());
            row.put("batch_year", s.getBatchYear());
            row.put("admission_year", s.getAdmissionYear());
            row.put("hostel_name", s.getHostelName());
            row.put("room_no", s.getRoomNo());
            row.put("email", s.getEmail());
            row.put("phone", s.getPhone());
            return row;
        }).toList();
    }

    @Tool(description = "Get comprehensive academic information for all students.")
    public List<Map<String, Object>> get_all_students_academic_information() {
        List<Student> students = studentRepository.findAllByOrderByRollNoAsc();
        if (students.isEmpty()) {
            return List.of();
        }

        List<String> studentIds = students.stream().map(Student::getStudentId).toList();

        Map<String, List<AcademicPerformance>> perfByStudent = academicPerformanceRepository.findByStudentIdIn(studentIds)
                .stream()
                .collect(Collectors.groupingBy(AcademicPerformance::getStudentId));

        Map<String, Placement> placementByStudent = placementRepository.findByStudentIdIn(studentIds)
                .stream()
                .collect(Collectors.toMap(
                        Placement::getStudentId,
                        p -> p,
                        (a, b) -> a.getPlacementId() >= b.getPlacementId() ? a : b
                ));

        Map<String, Internship> internshipByStudent = internshipRepository.findByStudentIdIn(studentIds)
                .stream()
                .collect(Collectors.toMap(
                        Internship::getStudentId,
                        i -> i,
                        (a, b) -> a.getInternshipId() >= b.getInternshipId() ? a : b
                ));

        return students.stream().map(student -> {
            AcademicPerformance ap = perfByStudent.getOrDefault(student.getStudentId(), List.of())
                    .stream()
                    .filter(x -> x.getSemester() != null && x.getSemester().equals(student.getSemester()))
                    .max(Comparator.comparing(AcademicPerformance::getResultId))
                    .orElse(null);

            Placement p = placementByStudent.get(student.getStudentId());
            Internship i = internshipByStudent.get(student.getStudentId());

            Map<String, Object> row = new LinkedHashMap<>();
            row.put("student_id", student.getStudentId());
            row.put("roll_no", student.getRollNo());
            row.put("name", buildName(student));
            row.put("department", student.getDepartment());
            row.put("semester", student.getSemester());
            row.put("sgpa", ap != null ? ap.getSgpa() : null);
            row.put("cgpa", ap != null ? ap.getCgpa() : null);
            row.put("backlogs", ap != null ? ap.getBacklogs() : null);
            row.put("academic_year", ap != null ? ap.getAcademicYear() : null);
            row.put("placement_company", p != null ? p.getCompanyName() : null);
            row.put("placement_role", p != null ? p.getRole() : null);
            row.put("package_lpa", p != null ? p.getPackageLpa() : null);
            row.put("placement_status", p != null ? p.getPlacementStatus() : null);
            row.put("internship_company", i != null ? i.getCompanyName() : null);
            row.put("internship_role", i != null ? i.getRole() : null);
            row.put("stipend", i != null ? i.getStipend() : null);
            return row;
        }).toList();
    }

    @Tool(description = "Get semester-wise metrics (attendance + SGPA/CGPA) for all students. Semester and year are optional (pass 0 to ignore).")
    public List<Map<String, Object>> admin_get_semester_metrics(
            @ToolParam(description = "Semester number, pass 0 for all") int semester,
            @ToolParam(description = "Calendar year, pass 0 for all") int year) {

        List<Student> students = semester > 0
                ? studentRepository.findBySemesterOrderByRollNoAsc(semester)
                : studentRepository.findAllByOrderByRollNoAsc();

        if (students.isEmpty()) {
            return List.of();
        }

        List<String> studentIds = students.stream().map(Student::getStudentId).toList();

        Map<String, List<StudentAttendance>> attendanceByStudent = studentAttendanceRepository.findByStudentIdIn(studentIds)
                .stream()
                .collect(Collectors.groupingBy(StudentAttendance::getStudentId));

        Map<String, List<AcademicPerformance>> perfByStudent = academicPerformanceRepository.findByStudentIdIn(studentIds)
                .stream()
                .collect(Collectors.groupingBy(AcademicPerformance::getStudentId));

        return students.stream().map(s -> {
            List<StudentAttendance> att = attendanceByStudent.getOrDefault(s.getStudentId(), List.of());
            int total = att.stream().mapToInt(a -> safeInt(a.getTotalClasses())).sum();
            int attended = att.stream().mapToInt(a -> safeInt(a.getAttendedClasses())).sum();
            BigDecimal attendancePct = BigDecimal.valueOf(total > 0 ? (attended * 100.0) / total : 0.0)
                    .setScale(2, RoundingMode.HALF_UP);

            List<AcademicPerformance> candidates = perfByStudent.getOrDefault(s.getStudentId(), List.of()).stream()
                    .filter(ap -> ap.getSemester() != null && ap.getSemester().equals(s.getSemester()))
                    .filter(ap -> year <= 0 || (ap.getAcademicYear() != null && ap.getAcademicYear().contains(String.valueOf(year))))
                    .toList();

            AcademicPerformance picked = candidates.stream()
                    .max(Comparator.comparing(AcademicPerformance::getResultId))
                    .orElse(null);

            Map<String, Object> row = new LinkedHashMap<>();
            row.put("student_id", s.getStudentId());
            row.put("roll_no", s.getRollNo());
            row.put("name", buildName(s));
            row.put("department", s.getDepartment());
            row.put("semester", s.getSemester());
            row.put("sgpa", picked != null ? picked.getSgpa() : null);
            row.put("cgpa", picked != null ? picked.getCgpa() : null);
            row.put("attendance_percentage", attendancePct);
            return row;
        }).toList();
    }

    private static String buildName(Student student) {
        String first = student.getFirstName() != null ? student.getFirstName().trim() : "";
        String last = student.getLastName() != null ? student.getLastName().trim() : "";
        return (first + " " + last).trim();
    }

    private static int safeInt(Integer value) {
        return value != null ? value : 0;
    }
}
