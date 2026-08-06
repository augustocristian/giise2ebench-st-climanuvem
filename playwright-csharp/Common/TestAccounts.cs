using System.Text;

namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// CSV loader and role lookup for system-test accounts. Mirrors
/// selenium-java's <c>TestAccounts</c>: loads
/// <c>role,email,password,verified,description</c> rows and groups them by
/// role.
/// </summary>
public sealed class TestAccounts
{
    public const string RoleLoginUser = "login_user";
    public const string RoleProfileUser = "profile_user";
    public const string RoleUnknownUser = "unknown_user";

    private readonly IReadOnlyList<TestAccount> _accounts;

    private TestAccounts(IReadOnlyList<TestAccount> accounts) => _accounts = accounts;

    public static TestAccounts Load(string accountsFile)
    {
        if (!File.Exists(accountsFile))
        {
            throw new FileNotFoundException(
                $"Accounts file not found: {accountsFile}. Create it from Resources/accounts.template.csv or set ACCOUNTS_FILE.");
        }

        var accounts = new List<TestAccount>();
        var headerSkipped = false;

        foreach (var rawLine in File.ReadLines(accountsFile))
        {
            var line = rawLine.Trim();
            if (line.Length == 0 || line.StartsWith('#'))
            {
                continue;
            }
            if (!headerSkipped)
            {
                headerSkipped = true;
                if (line.StartsWith("role,", StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }
            }
            accounts.Add(ParseLine(line, accountsFile));
        }

        return new TestAccounts(accounts);
    }

    public static TestAccounts Empty() => new([]);

    public IReadOnlyList<TestAccount> ByRole(string role) => _accounts.Where(a => a.Role == role).ToList();

    public TestAccount RequiredSingle(string role)
    {
        var matches = ByRole(role);
        if (matches.Count == 0)
        {
            throw new InvalidOperationException($"Configure at least one account with role '{role}' in ACCOUNTS_FILE.");
        }
        return matches[0];
    }

    public IReadOnlyList<TestAccount> Required(string role)
    {
        var matches = ByRole(role);
        if (matches.Count == 0)
        {
            throw new InvalidOperationException($"Configure at least one {role} in ACCOUNTS_FILE.");
        }
        return matches;
    }

    public IReadOnlyList<TestAccount> LoginAccounts() => Required(RoleLoginUser);
    public IReadOnlyList<TestAccount> ProfileAccounts() => Required(RoleProfileUser);
    public TestAccount LoginAccount() => RequiredSingle(RoleLoginUser);
    public TestAccount ProfileAccount() => RequiredSingle(RoleProfileUser);
    public TestAccount UnknownAccount() => RequiredSingle(RoleUnknownUser);

    private static TestAccount ParseLine(string line, string accountsFile)
    {
        var columns = SplitCsvLine(line);
        if (columns.Count < 5)
        {
            throw new InvalidOperationException(
                $"Invalid accounts row in {accountsFile}. Expected columns: role,email,password,verified,description. Row: {line}");
        }
        return new TestAccount(
            columns[0].Trim(),
            columns[1].Trim(),
            columns[2],
            columns[3].Trim().Equals("true", StringComparison.OrdinalIgnoreCase),
            columns[4].Trim());
    }

    private static List<string> SplitCsvLine(string line)
    {
        var values = new List<string>();
        var current = new StringBuilder();
        var quoted = false;

        for (var i = 0; i < line.Length; i++)
        {
            var ch = line[i];
            if (ch == '"')
            {
                if (quoted && i + 1 < line.Length && line[i + 1] == '"')
                {
                    current.Append('"');
                    i++;
                }
                else
                {
                    quoted = !quoted;
                }
            }
            else if (ch == ',' && !quoted)
            {
                values.Add(current.ToString());
                current.Clear();
            }
            else
            {
                current.Append(ch);
            }
        }
        values.Add(current.ToString());
        return values;
    }
}
