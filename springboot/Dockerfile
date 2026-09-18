# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-25-alpine AS builder

WORKDIR /app

# Descargar dependencias primero (capa cacheada — solo se invalida si cambia pom.xml)
COPY pom.xml .
RUN mvn dependency:go-offline -q

COPY src ./src
RUN mvn package -DskipTests -q

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM eclipse-temurin:25-jre-alpine AS runtime

LABEL maintainer="MarketMind IA Team"
LABEL description="Spring Boot API de cara al cliente — solo lectura + aprobación de campañas"

WORKDIR /app

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/target/marketmind-springboot-*.jar app.jar
RUN chown appuser:appgroup app.jar

USER appuser

EXPOSE 8080

# Render asigna PORT dinámicamente — sh -c expande la variable antes de pasarla a java.
ENTRYPOINT ["sh", "-c", "java -Dserver.port=${PORT:-8080} -jar app.jar"]
