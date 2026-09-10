package com.juhee.portfolio_backend.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOriginPatterns(
                        "http://localhost:3000",
                        "https://kangjuhee-portfolio.vercel.app",
                        "https://kangjuhee-portfolio-*.vercel.app",
                        "https://kangjuhee-portfolio-*-1thorn1s-projects.vercel.app",
                        "https://portfolio-frontend-one-pearl.vercel.app",
                        "https://portfolio-frontend-*-1thorn1s-projects.vercel.app"
                )
                .allowedMethods("GET", "POST", "PUT", "DELETE", "PATCH")
                .allowedHeaders("*");
    }
}
