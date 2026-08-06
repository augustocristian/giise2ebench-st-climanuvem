package epigijon.climanuvem.e2e.functional.common;

public class TestAccount {

    private final String role;
    private final String email;
    private final String password;
    private final boolean verified;
    private final String description;

    public TestAccount(String role, String email, String password, boolean verified, String description) {
        this.role = role;
        this.email = email;
        this.password = password;
        this.verified = verified;
        this.description = description;
    }

    public String getRole() {
        return role;
    }

    public String getEmail() {
        return email;
    }

    public String getPassword() {
        return password;
    }

    public boolean isVerified() {
        return verified;
    }

    public String getDescription() {
        return description;
    }

    @Override
    public String toString() {
        return role + ":" + email;
    }
}
