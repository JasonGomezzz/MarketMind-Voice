package com.marketmind.security;

import com.marketmind.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.Objects;
import java.util.Optional;

/** Shared HTTP/socket check against Django's current user and revocation version. */
@Component
@RequiredArgsConstructor
public class CurrentUserVerifier {
    private final UserRepository userRepository;

    // Scalar projection reads current database values even during an AFTER_COMMIT callback,
    // without reusing cached entities or borrowing a second connection for each delivery.
    public Optional<CurrentUserSnapshot> findCurrent(AuthenticatedUser user) {
        return userRepository.findCurrentSnapshotById(user.userId())
                .filter(entity -> Boolean.TRUE.equals(entity.active()))
                .filter(entity -> Objects.equals(entity.role(), user.role()))
                .filter(entity -> user.tokenVersion() == null
                        ? entity.tokenVersion() == null || entity.tokenVersion() == 0
                        : Objects.equals(entity.tokenVersion(), user.tokenVersion()));
    }
}
