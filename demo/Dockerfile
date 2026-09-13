# Spring Boot MCP/REST service image for Render (build context: demo/)
FROM maven:3.9-eclipse-temurin-17 AS build

WORKDIR /build
COPY pom.xml ./
RUN mvn -B -DskipTests dependency:go-offline
COPY src src
RUN mvn -B -DskipTests package

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build /build/target/*.jar app.jar

# Spring reads Render's PORT through application.properties.
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
