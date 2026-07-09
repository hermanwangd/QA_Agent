package pirun.heavyjdbc;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

class RedactorTest {
    @Test
    void redactsJdbcConnectionPasswordAndBearerTokenFromCapturedOutput() {
        String jdbcConnection = "jdbc:oracle:thin:APP/PirunSecret123@localhost:1521/freepdb1";
        String output = ""
            + "connection=" + jdbcConnection + "\n"
            + "password=PirunSecret123\n"
            + "Authorization: Bearer abc.def.ghi\n";

        String redacted = Redactor.redact(output, List.of(jdbcConnection, "PirunSecret123"));

        assertFalse(redacted.contains(jdbcConnection));
        assertFalse(redacted.contains("PirunSecret123"));
        assertFalse(redacted.contains("abc.def.ghi"));
        assertTrue(redacted.contains("[REDACTED]"));
    }
}
