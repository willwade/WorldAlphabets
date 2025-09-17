using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;

namespace WorldAlphabets.Utils;

internal static class ResourceLoader
{
    private static readonly Assembly Assembly = typeof(ResourceLoader).Assembly;
    private static readonly string Prefix = Assembly.GetName().Name + ".Resources.";

    public static string ReadText(string logicalPath)
    {
        using var stream = Open(logicalPath) ?? throw new FileNotFoundException($"Resource not found: {logicalPath}");
        using var reader = new StreamReader(stream, Encoding.UTF8);
        return reader.ReadToEnd();
    }

    public static Stream? Open(string logicalPath)
    {
        var resourceName = Prefix + logicalPath.Replace('/', '.').Replace('\\', '.');
        return Assembly.GetManifestResourceStream(resourceName);
    }

    public static IEnumerable<string> Enumerate(string folder)
    {
        var targetPrefix = Prefix + folder.Replace('/', '.').TrimEnd('.') + ".";
        foreach (var name in Assembly.GetManifestResourceNames())
        {
            if (name.StartsWith(targetPrefix, StringComparison.Ordinal))
            {
                yield return name.Substring(targetPrefix.Length);
            }
        }
    }
}

