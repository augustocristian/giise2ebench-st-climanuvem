using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Formats.Jpeg;
using SixLabors.ImageSharp.PixelFormats;

namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Synthesizes the same JPEG fixtures selenium-java's <c>BaseApiClass</c>
/// built with <c>java.awt.Graphics2D</c>, using SixLabors.ImageSharp's raw
/// pixel indexer instead (no shape-drawing package needed for a couple of
/// filled ellipses/rectangles).
/// </summary>
public static class TestImages
{
    private const int TooLargePayloadSize = 5 * 1024 * 1024 + 1;

    /// <summary>Minimal 10x10 solid JPEG — small and fast, valid enough for the upload endpoint.</summary>
    public static byte[] CreateTestImage()
    {
        using var image = new Image<Rgb24>(10, 10);
        FillRect(image, 0, 0, 10, 10, new Rgb24(200, 200, 200));
        return ToJpegBytes(image);
    }

    /// <summary>640x360 blue sky with a handful of overlapping white/grey cloud ellipses.</summary>
    public static byte[] CreateCloudyJpeg()
    {
        const int width = 640;
        const int height = 360;
        using var image = new Image<Rgb24>(width, height);
        FillRect(image, 0, 0, width, height, new Rgb24(98, 171, 232));

        var cloud = new Rgb24(245, 248, 250);
        FillEllipse(image, 210, 142, 90, 47, cloud);
        FillEllipse(image, 340, 132, 105, 62, cloud);
        FillEllipse(image, 455, 155, 75, 40, cloud);
        FillRect(image, 175, 145, 310, 75, cloud);
        FillEllipse(image, 295, 202, 85, 27, new Rgb24(225, 232, 238));

        return ToJpegBytes(image);
    }

    /// <summary>640x360 clear vertical sky gradient — no clouds.</summary>
    public static byte[] CreateNoCloudJpeg()
    {
        const int width = 640;
        const int height = 360;
        using var image = new Image<Rgb24>(width, height);

        for (var y = 0; y < height; y++)
        {
            var ratio = (float)y / height;
            var r = (byte)(70 + Math.Round(35 * ratio));
            var g = (byte)(155 + Math.Round(45 * ratio));
            var b = (byte)(225 + Math.Round(25 * ratio));
            FillRect(image, 0, y, width, 1, new Rgb24(r, g, b));
        }

        return ToJpegBytes(image);
    }

    public static byte[] CreateEmptyImageBytes() => [];

    /// <summary>A valid small JPEG followed by junk bytes, padded past the 5 MB upload limit.</summary>
    public static byte[] CreateTooLargePayload()
    {
        var validJpeg = CreateTestImage();
        var payload = new byte[TooLargePayloadSize];
        Array.Copy(validJpeg, payload, validJpeg.Length);
        for (var i = validJpeg.Length; i < payload.Length; i++)
        {
            payload[i] = (byte)(i % 251);
        }
        return payload;
    }

    public static byte[] CreateNonJpegPayload() => "not-a-jpeg-image"u8.ToArray();

    private static void FillRect(Image<Rgb24> image, int x0, int y0, int w, int h, Rgb24 color)
    {
        var xEnd = Math.Min(image.Width, x0 + w);
        var yEnd = Math.Min(image.Height, y0 + h);
        for (var y = Math.Max(0, y0); y < yEnd; y++)
        {
            for (var x = Math.Max(0, x0); x < xEnd; x++)
            {
                image[x, y] = color;
            }
        }
    }

    private static void FillEllipse(Image<Rgb24> image, double cx, double cy, double rx, double ry, Rgb24 color)
    {
        var top = Math.Max(0, (int)Math.Floor(cy - ry));
        var bottom = Math.Min(image.Height, (int)Math.Ceiling(cy + ry));
        for (var y = top; y < bottom; y++)
        {
            var dy = (y - cy) / ry;
            var spanSq = 1 - dy * dy;
            if (spanSq < 0)
            {
                continue;
            }
            var span = rx * Math.Sqrt(spanSq);
            var left = Math.Max(0, (int)Math.Round(cx - span));
            var right = Math.Min(image.Width, (int)Math.Round(cx + span));
            for (var x = left; x < right; x++)
            {
                image[x, y] = color;
            }
        }
    }

    private static byte[] ToJpegBytes(Image<Rgb24> image)
    {
        using var stream = new MemoryStream();
        image.Save(stream, new JpegEncoder { Quality = 90 });
        return stream.ToArray();
    }
}
