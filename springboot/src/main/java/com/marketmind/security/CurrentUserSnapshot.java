package com.marketmind.security;

/** Scalar query result; cannot reuse a stale UserEntity from JPA's first-level cache. */
public record CurrentUserSnapshot(String email, String role, Boolean active, Integer tokenVersion) {}
