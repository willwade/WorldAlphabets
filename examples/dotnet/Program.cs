using System;
using WorldAlphabets.Api;

class Program
{
    static void Main()
    {
        var codes = WorldAlphabets.GetAvailableCodes();
        Console.WriteLine($"Loaded {codes.Count} alphabets (first 5): {string.Join(", ", codes.GetRange(0, Math.Min(5, codes.Count)))}");

        var scriptsSr = WorldAlphabets.GetScripts("sr");
        Console.WriteLine($"Serbian scripts: {string.Join(", ", scriptsSr)}");

        var alphabet = WorldAlphabets.LoadAlphabet("fr");
        Console.WriteLine($"French lowercase (first 5): {string.Join(" ", alphabet.Lowercase.GetRange(0, Math.Min(5, alphabet.Lowercase.Count)))}");

        var res = WorldAlphabets.OptimizedDetectLanguages("Hello world");
        Console.WriteLine($"Detected: {string.Join(", ", res.Select(r => $"{r.lang}:{r.score:F3}"))}");

        var layouts = WorldAlphabets.GetAvailableLayouts();
        Console.WriteLine($"Layouts (first 5): {string.Join(", ", layouts.Take(5))}");
    }
}

