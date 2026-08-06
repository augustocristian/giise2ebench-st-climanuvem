namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Account row used by parameterized system tests. Mirrors selenium-java's
/// <c>TestAccount</c>.
/// </summary>
public sealed record TestAccount(string Role, string Email, string Password, bool Verified, string Description)
{
    public override string ToString() => $"{Role}:{Email}";
}
