package pirun.heavyjdbc;

import java.util.List;
import java.util.regex.Pattern;

final class Redactor {
    private static final Pattern PASSWORD_ASSIGNMENT = Pattern.compile("(?i)(password\\s*[=:]\\s*)([^\\s,;]+)");
    private static final Pattern BEARER_TOKEN = Pattern.compile("(?i)(authorization\\s*:\\s*bearer\\s+)([^\\s]+)");

    private Redactor() {
    }

    static String redact(String value, List<String> exactSecrets) {
        if (value == null || value.isEmpty()) {
            return value;
        }

        String redacted = value;
        for (String secret : exactSecrets) {
            if (secret != null && !secret.isBlank()) {
                redacted = redacted.replace(secret, "[REDACTED]");
            }
        }

        redacted = PASSWORD_ASSIGNMENT.matcher(redacted).replaceAll("$1[REDACTED]");
        return BEARER_TOKEN.matcher(redacted).replaceAll("$1[REDACTED]");
    }
}
