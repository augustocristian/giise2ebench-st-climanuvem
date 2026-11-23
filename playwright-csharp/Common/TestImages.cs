namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// JPEG fixtures for the upload endpoint. The three real images are checked-in files under
/// <c>Resources/images</c> (a 10x10 grey square, a cloudy sky and a clear sky), so no image
/// library is needed at test time. The invalid payloads are derived from bytes.
/// </summary>
public static class TestImages
{
    private const int TooLargePayloadSize = 5 * 1024 * 1024 + 1;

    /// <summary>Minimal valid JPEG: small and fast, accepted by the upload endpoint.</summary>
    public static byte[] Tiny() => Load("tiny.jpg");

    /// <summary>640x360 blue sky with overlapping white/grey clouds.</summary>
    public static byte[] Cloudy() => Load("cloudy.jpg");

    /// <summary>640x360 clear vertical sky gradient, no clouds.</summary>
    public static byte[] ClearSky() => Load("clear-sky.jpg");

    /// <summary>A valid small JPEG followed by filler bytes, just past the 5 MB upload limit.</summary>
    public static byte[] TooLarge()
    {
        var payload = new byte[TooLargePayloadSize];
        Tiny().CopyTo(payload, 0);
        return payload;
    }

    public static byte[] NotAJpeg() => "not-a-jpeg-image"u8.ToArray();

    private static byte[] Load(string name) =>
        File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory, "Resources", "images", name));
}
