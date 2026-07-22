package com.juhee.portfolio_backend.visitor;

import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;

public interface VisitorRepository extends JpaRepository<Visitor, Long> {

    boolean existsByIpAddressAndVisitDate(String ipAddress, LocalDate visitDate);
}
