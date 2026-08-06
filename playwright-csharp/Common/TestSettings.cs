namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Environment-driven configuration, equivalent to selenium-java's
/// <c>test.properties</c> + system-property/env-var overrides, collapsed
/// into a single environment-variable tier (the standard config mechanism
/// for a dotnet-test-based suite).
/// </summary>
public static class TestSettings
{
    public static string SutUrl => GetString("SUT_URL", "http://localhost:8000");
    public static string FrontendUrl => GetString("FRONTEND_URL", "http://localhost:5173");
    public static string TestToken => GetString("TEST_TOKEN", "test-token-climanuvem");
    public static int HttpTimeoutMs => GetInt("HTTP_TIMEOUT_MS", 10_000);
    public static int AnalysisTimeoutMs => GetInt("ANALYSIS_TIMEOUT_MS", 360_000);
    public static string AccountsFile => GetString("ACCOUNTS_FILE", "Resources/accounts.local.csv");
    public static string RegisterEmailDomain => GetString("REGISTER_EMAIL_DOMAIN", "gmail.com");
    public static string FirebaseWebApiKey => GetString("FIREBASE_WEB_API_KEY", "");
    public static bool RealOllamaTests => GetBool("REAL_OLLAMA_TESTS", false);
    public static bool Ci => GetBool("CI", false);

    private static string GetString(string key, string fallback) =>
        Environment.GetEnvironmentVariable(key) is { Length: > 0 } value ? value : fallback;

    private static int GetInt(string key, int fallback)
    {
        var value = Environment.GetEnvironmentVariable(key);
        return value is { Length: > 0 } && int.TryParse(value, out var parsed) ? parsed : fallback;
    }

    private static bool GetBool(string key, bool fallback)
    {
        var value = Environment.GetEnvironmentVariable(key);
        return value is { Length: > 0 } ? value.Equals("true", StringComparison.OrdinalIgnoreCase) : fallback;
    }
}
