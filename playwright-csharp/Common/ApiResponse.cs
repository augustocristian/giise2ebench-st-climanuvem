using System.Text;
using System.Text.Json;

namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Fully-read HTTP response (status, headers, body), so the underlying Playwright response can be
/// disposed right away and tests can assert on any part of it.
/// </summary>
public sealed record ApiResponse(int Status, IReadOnlyDictionary<string, string> Headers, byte[] Body)
{
    public string Text => Encoding.UTF8.GetString(Body);

    public JsonElement Json => JsonDocument.Parse(Body).RootElement;

    /// <summary>Header value by case-insensitive name, or null when absent.</summary>
    public string? Header(string name) =>
        Headers.FirstOrDefault(h => string.Equals(h.Key, name, StringComparison.OrdinalIgnoreCase)).Value;
}
