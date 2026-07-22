package com.juhee.portfolio_backend.visitor;

import org.springframework.stereotype.Service;

import java.time.LocalDate;

@Service
public class VisitorService {

    private final VisitorRepository visitorRepository;

    public VisitorService(VisitorRepository visitorRepository) {
        this.visitorRepository = visitorRepository;
    }

    public long registerVisitAndGetTotalCount(String ipAddress) {
        LocalDate today = LocalDate.now();
        if (!visitorRepository.existsByIpAddressAndVisitDate(ipAddress, today)) {
            visitorRepository.save(new Visitor(ipAddress, today));
        }
        return visitorRepository.count();
    }
}
