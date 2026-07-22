package com.juhee.portfolio_backend.visitor;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.LocalDate;

@Entity
@Table(name = "visitor_log", uniqueConstraints = @UniqueConstraint(columnNames = {"ip_address", "visit_date"}))
public class Visitor {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "ip_address", nullable = false)
    private String ipAddress;

    @Column(name = "visit_date", nullable = false)
    private LocalDate visitDate;

    protected Visitor() {
    }

    public Visitor(String ipAddress, LocalDate visitDate) {
        this.ipAddress = ipAddress;
        this.visitDate = visitDate;
    }

    public Long getId() {
        return id;
    }

    public String getIpAddress() {
        return ipAddress;
    }

    public LocalDate getVisitDate() {
        return visitDate;
    }
}
