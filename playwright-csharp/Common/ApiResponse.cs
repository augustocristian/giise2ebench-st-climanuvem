using System.Text.Json;

namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Wraps an HTTP response's status code and body together, mirroring
/// selenium-java's <c>BaseApiClass.ApiResponse</c> — used where a test
/// needs to assert on both at once (e.g. the real-Ollama upload flow).
/// </summary>
public sealed record ApiResponse(int StatusCode, string Body)
{
    public JsonElement Json => JsonDocument.Parse(Body).RootElement;
}
