package pirun.heavyjdbc;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.TimeUnit;

final class SuiteMaterializer {
    private SuiteMaterializer() {
    }

    static Path materialize(
        Path repoRoot,
        String runId,
        String frameworkVersion,
        String providerId,
        String dialect,
        String profile
    ) throws IOException, InterruptedException {
        return materializeWithFunction(
            repoRoot,
            runId,
            frameworkVersion,
            providerId,
            dialect,
            profile,
            "materialize_heavy_jdbc_container"
        );
    }

    static Path materializeCrud(
        Path repoRoot,
        String runId,
        String frameworkVersion,
        String providerId,
        String dialect,
        String profile
    ) throws IOException, InterruptedException {
        return materializeWithFunction(
            repoRoot,
            runId,
            frameworkVersion,
            providerId,
            dialect,
            profile,
            "materialize_heavy_jdbc_crud_container"
        );
    }

    private static Path materializeWithFunction(
        Path repoRoot,
        String runId,
        String frameworkVersion,
        String providerId,
        String dialect,
        String profile,
        String materializerFunction
    ) throws IOException, InterruptedException {
        Path runDir = repoRoot
            .resolve(".pirun")
            .resolve("runs")
            .resolve(runId)
            .resolve("jdbc_" + dialect + "_testcontainers");
        Path samplesRoot = repoRoot
            .resolve("artifacts/usage-kits/usage-kit-v" + frameworkVersion)
            .resolve("usage-kit")
            .resolve("samples");

        String script = """
            import sys
            from pathlib import Path

            repo_root = Path(sys.argv[1]).resolve()
            sys.path.insert(0, str(repo_root))

            from pirun.materialize import contract_baseline

            materializer = getattr(contract_baseline, sys.argv[7])
            materializer(
                run_dir=Path(sys.argv[2]),
                provider_id=sys.argv[3],
                dialect=sys.argv[4],
                connection_secret_ref="env://JDBC_CONNECTION",
                profile=sys.argv[5],
                samples_root=Path(sys.argv[6]),
            )
            """;

        ProcessBuilder pb = new ProcessBuilder(
            List.of(
                "python3",
                "-c",
                script,
                repoRoot.toString(),
                runDir.toString(),
                providerId,
                dialect,
                profile,
                samplesRoot.toString(),
                materializerFunction
            )
        );
        pb.directory(repoRoot.toFile());
        Process process = pb.start();
        boolean finished = process.waitFor(Duration.ofSeconds(30).toSeconds(), TimeUnit.SECONDS);
        if (!finished) {
            process.destroyForcibly();
            process.waitFor(10, TimeUnit.SECONDS);
            String stdout = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            String stderr = new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8);
            throw new IOException("suite materializer timed out\nstdout:\n" + stdout + "\nstderr:\n" + stderr);
        }
        String stdout = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        String stderr = new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8);
        if (process.exitValue() != 0) {
            throw new IOException("suite materializer failed\nstdout:\n" + stdout + "\nstderr:\n" + stderr);
        }
        Files.createDirectories(runDir);
        return runDir;
    }
}
