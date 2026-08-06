package epigijon.climanuvem.e2e.functional.common;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

public class TestAccounts {

    public static final String ROLE_LOGIN_USER = "login_user";
    public static final String ROLE_PROFILE_USER = "profile_user";
    public static final String ROLE_UNKNOWN_USER = "unknown_user";

    private final List<TestAccount> accounts;

    private TestAccounts(List<TestAccount> accounts) {
        this.accounts = accounts;
    }

    public static TestAccounts load(String accountsFile) throws IOException {
        Path path = Paths.get(accountsFile);
        if (!Files.exists(path)) {
            throw new IOException("Accounts file not found: " + accountsFile
                    + ". Create it from src/test/resources/accounts.template.csv or set ACCOUNTS_FILE.");
        }

        List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
        List<TestAccount> parsed = new ArrayList<>();
        boolean headerSkipped = false;
        for (String line : lines) {
            String trimmed = line.trim();
            if (trimmed.isEmpty() || trimmed.startsWith("#")) {
                continue;
            }
            if (!headerSkipped) {
                headerSkipped = true;
                if (trimmed.toLowerCase().startsWith("role,")) {
                    continue;
                }
            }
            parsed.add(parseLine(trimmed, accountsFile));
        }
        return new TestAccounts(Collections.unmodifiableList(parsed));
    }

    public static TestAccounts empty() {
        return new TestAccounts(Collections.emptyList());
    }

    public List<TestAccount> byRole(String role) {
        return accounts.stream()
                .filter(account -> role.equals(account.getRole()))
                .collect(Collectors.toList());
    }

    public TestAccount requiredSingle(String role) {
        List<TestAccount> matches = byRole(role);
        if (matches.isEmpty()) {
            throw new AssertionError("Configure at least one account with role '" + role + "' in ACCOUNTS_FILE.");
        }
        return matches.get(0);
    }

    private static TestAccount parseLine(String line, String accountsFile) {
        List<String> columns = splitCsv(line);
        if (columns.size() < 5) {
            throw new IllegalArgumentException("Invalid accounts row in " + accountsFile
                    + ". Expected columns: role,email,password,verified,description. Row: " + line);
        }
        return new TestAccount(
                columns.get(0).trim(),
                columns.get(1).trim(),
                columns.get(2),
                Boolean.parseBoolean(columns.get(3).trim()),
                columns.get(4).trim());
    }

    private static List<String> splitCsv(String line) {
        List<String> values = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        boolean quoted = false;
        for (int i = 0; i < line.length(); i++) {
            char ch = line.charAt(i);
            if (ch == '"') {
                if (quoted && i + 1 < line.length() && line.charAt(i + 1) == '"') {
                    current.append('"');
                    i++;
                } else {
                    quoted = !quoted;
                }
            } else if (ch == ',' && !quoted) {
                values.add(current.toString());
                current.setLength(0);
            } else {
                current.append(ch);
            }
        }
        values.add(current.toString());
        return values;
    }
}
