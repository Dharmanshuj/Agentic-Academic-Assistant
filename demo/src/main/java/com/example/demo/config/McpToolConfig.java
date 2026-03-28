package com.example.demo.config;

import com.example.demo.service.PayrollToolService;
import org.springframework.ai.tool.ToolCallbackProvider;
import org.springframework.ai.tool.method.MethodToolCallbackProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class McpToolConfig {

    @Bean
    public ToolCallbackProvider payrollTools(PayrollToolService payrollToolService) {
        return MethodToolCallbackProvider.builder()
                .toolObjects(payrollToolService)
                .build();
    }
}
