package com.example.demo.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.JwtException;
import io.github.cdimascio.dotenv.Dotenv;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;

@Service
public class JwtTokenService {

    private final SecretKey signingKey;

    public JwtTokenService(@Value("${SECRET_KEY:}") String configuredSecretKey) {
        String secretKey = resolveSecretKey(configuredSecretKey);
        if (secretKey == null || secretKey.isBlank()) {
            throw new IllegalStateException("SECRET_KEY must be configured for JWT validation.");
        }
        this.signingKey = new SecretKeySpec(
                secretKey.getBytes(StandardCharsets.UTF_8),
                "HmacSHA256"
        );
    }

    private String resolveSecretKey(String configuredSecretKey) {
        if (configuredSecretKey != null && !configuredSecretKey.isBlank()) {
            return configuredSecretKey;
        }

        String systemProperty = System.getProperty("SECRET_KEY");
        if (systemProperty != null && !systemProperty.isBlank()) {
            return systemProperty;
        }

        String envValue = System.getenv("SECRET_KEY");
        if (envValue != null && !envValue.isBlank()) {
            return envValue;
        }

        Dotenv rootDotenv = Dotenv.configure()
                .directory("..")
                .ignoreIfMissing()
                .load();
        String rootValue = rootDotenv.get("SECRET_KEY");
        if (rootValue != null && !rootValue.isBlank()) {
            return rootValue;
        }

        Dotenv resourceDotenv = Dotenv.configure()
                .directory("src/main/resources")
                .ignoreIfMissing()
                .load();
        return resourceDotenv.get("SECRET_KEY");
    }

    public Claims parseToken(String token) throws JwtException {
        return Jwts.parser()
                .verifyWith(signingKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
