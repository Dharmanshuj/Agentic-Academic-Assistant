package com.example.demo.config;

import com.example.demo.service.StudentToolService;
import org.springframework.ai.tool.ToolCallbackProvider;
import org.springframework.ai.tool.method.MethodToolCallbackProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class McpToolConfig {

    @Bean
    public ToolCallbackProvider studentTools(StudentToolService studentToolService) {
        return MethodToolCallbackProvider.builder()
                .toolObjects(studentToolService)
                .build();
    }
}
