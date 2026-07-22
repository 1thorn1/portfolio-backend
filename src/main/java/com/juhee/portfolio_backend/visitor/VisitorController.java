package com.juhee.portfolio_backend.visitor;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/visitors")
public class VisitorController {

    private final VisitorService visitorService;

    public VisitorController(VisitorService visitorService) {
        this.visitorService = visitorService;
    }

    @GetMapping("/count")
    public VisitorCountResponse getCount(HttpServletRequest request) {
        String ipAddress = resolveClientIp(request);
        long totalCount = visitorService.registerVisitAndGetTotalCount(ipAddress);
        return new VisitorCountResponse(totalCount);
    }

    private String resolveClientIp(HttpServletRequest request) {
        String forwardedFor = request.getHeader("X-Forwarded-For");
        if (forwardedFor != null && !forwardedFor.isBlank()) {
            return forwardedFor.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }

    public record VisitorCountResponse(long totalCount) {
    }
}
