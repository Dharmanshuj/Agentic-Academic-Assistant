package com.example.demo.service;

import com.example.demo.model.Attendance;
import com.example.demo.model.Employee;
import com.example.demo.model.SalaryPayment;

public class PyrollCalculationLogic {

    public SalaryPayment generateSalaryPayment(Employee e, Attendance a) {

        SalaryPayment s = new SalaryPayment();

        s.setEmpno(e.getEmpno());
        s.setMonth(a.getMonth());
        s.setYear(a.getYear());
        s.setAttendanceId(a.getId());

        double gross = e.getGrossSalary();

        int totalDays = a.getTotalDays();
        int presentDays = Math.min(a.getPresentDays(), totalDays);

        double perDay = gross / totalDays;
        double earned = perDay * presentDays;

        s.setGrossSalary(gross);
        s.setPerDaySalary(perDay);
        s.setEarnedSalary(earned);

        s.setTotalDeductions(e.getTotalDeductions());

        s.setFinalSalary(earned - e.getTotalDeductions());

        return s;
    }
}
