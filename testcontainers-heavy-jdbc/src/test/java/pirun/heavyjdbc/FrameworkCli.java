package pirun.heavyjdbc;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

final class FrameworkCli {
    private FrameworkCli() {
    }

    static Result run(
        Path repoRoot,
        Path runDir,
        String frameworkVersion,
        String profile,
        String jdbcConnection,
        String username,
        String password
    ) throws IOException, InterruptedException {
        Path frameworkJar = repoRoot
            .resolve("artifacts/release-assets/release-assets-v" + frameworkVersion)
            .resolve("spec-driven-auto-regression-" + frameworkVersion + ".jar");
        Path usageKitRoot = repoRoot
            .resolve("artifacts/usage-kits/usage-kit-v" + frameworkVersion)
            .resolve("usage-kit");
        String javaClasspath = System.getProperty("java.class.path", "");
        String processClasspath = frameworkJar + File.pathSeparator + javaClasspath;

        List<String> command = new ArrayList<>();
        command.add(javaBinary());
        command.add("-Xmx512m");
        command.add("-Dloader.main=com.specdriven.regression.RegressionApplication");
        // Spring Boot PropertiesLauncher supports loader.path for extra classpath locations.
        // Source: https://docs.spring.io/spring-boot/specification/executable-jar/property-launcher.html
        command.add("-Dloader.path=" + toLoaderPath(javaClasspath));
        command.add("-cp");
        command.add(processClasspath);
        command.add("org.springframework.boot.loader.launch.PropertiesLauncher");
        command.add("run");
        command.add("--suite");
        command.add(runDir.resolve("suite_manifest.yaml").toString());
        command.add("--profile");
        command.add(profile);

        ProcessBuilder pb = new ProcessBuilder(command);
        pb.directory(usageKitRoot.toFile());
        Map<String, String> env = pb.environment();
        env.put("PIRUN_JDBC_CONNECTION", jdbcConnection);
        env.put("PIRUN_JDBC_USERNAME", username);
        env.put("PIRUN_JDBC_PASSWORD", password);

        Process process = pb.start();
        boolean finished = process.waitFor(Duration.ofMinutes(3).toSeconds(), TimeUnit.SECONDS);
        if (!finished) {
            process.destroyForcibly();
            process.waitFor(10, TimeUnit.SECONDS);
            String stdout = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            String stderr = new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8);
            return new Result(124, stdout, stderr + "\nframework_timeout: PT3M", command);
        }
        String stdout = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        String stderr = new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8);
        return new Result(process.exitValue(), stdout, stderr, command);
    }

    private static String javaBinary() {
        return Path.of(System.getProperty("java.home"), "bin", "java").toString();
    }

    private static String toLoaderPath(String javaClasspath) {
        return javaClasspath.replace(File.pathSeparator, ",");
    }

    record Result(int exitCode, String stdout, String stderr, List<String> command) {
        void writeTo(Path runDir) throws IOException {
            Files.createDirectories(runDir);
            Files.writeString(runDir.resolve("framework_stdout.txt"), stdout, StandardCharsets.UTF_8);
            Files.writeString(runDir.resolve("framework_stderr.txt"), stderr, StandardCharsets.UTF_8);
            Files.writeString(
                runDir.resolve("framework_invocation.json"),
                "{\n"
                    + "  \"exit_code\": " + exitCode + ",\n"
                    + "  \"command\": " + jsonString(command.toString()) + "\n"
                    + "}\n",
                StandardCharsets.UTF_8
            );
        }
    }

    private static String jsonString(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\"";
    }
}
