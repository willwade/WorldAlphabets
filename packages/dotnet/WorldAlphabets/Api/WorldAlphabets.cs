using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using WorldAlphabets.Models;
using WorldAlphabets.Utils;

namespace WorldAlphabets;

/// <summary>
/// Static facade exposing WorldAlphabets data (alphabets, keyboards, index)
/// and utilities (diacritics, detection) for .NET.
/// </summary>

public static class WorldAlphabets
{
    private static List<IndexEntry>? _index;

    private static List<IndexEntry> LoadIndex()
    {
        if (_index != null) return _index;
        var json = ResourceLoader.ReadText("index.json");
        _index = JsonSerializer.Deserialize<List<IndexEntry>>(json) ?? new();
        return _index;
    }

    /// <summary>Returns the raw index entries describing available languages and scripts.</summary>

    public static IReadOnlyList<IndexEntry> GetIndexData() => LoadIndex();

    /// <summary>Lists all available ISO language codes present in the dataset.</summary>
    public static List<string> GetAvailableCodes()
        => LoadIndex().Select(i => i.Language).Distinct().OrderBy(x => x).ToList();
    /// <summary>Returns the available scripts for a given language code.</summary>
    /// <param name="langCode">ISO/BCP-47 code (e.g. "sr", "en").</param>


    public static List<string> GetScripts(string langCode)
    {
        var entries = LoadIndex().Where(i => i.Language == langCode).ToList();
        var scripts = new List<string>();
        foreach (var e in entries)
        {
            if (!string.IsNullOrEmpty(e.Script)) scripts.Add(e.Script!);
            if (e.Scripts != null) scripts.AddRange(e.Scripts);

        }
        return scripts.Distinct().ToList();
    }

    /// <summary>Loads the alphabet for a language (optionally a specific script).</summary>
    /// <param name="code">Language code, e.g. "en".</param>
    /// <param name="script">Optional script (e.g. "Latn"). If null, uses the first script from the index.</param>
    /// <exception cref="FileNotFoundException">Thrown when the alphabet cannot be found.</exception>

    public static Models.Alphabet LoadAlphabet(string code, string? script = null)
    {
        var res = TryGetAlphabet(code, script);
        if (res == null) throw new FileNotFoundException($"Alphabet data for code '{code}' not found");

        return res;
    }

    internal static Models.Alphabet? TryGetAlphabet(string code, string? script = null)
    {
        if (string.IsNullOrEmpty(script))
        {
            // pick first script from index if available
            var first = LoadIndex().FirstOrDefault(i => i.Language == code);
            script = first?.Script ?? first?.Scripts?.FirstOrDefault();
        }

        foreach (var candidate in AlphabetCandidates(code, script))
        {
            try
            {
                using var s = ResourceLoader.Open(candidate);
                if (s == null) continue;
                return JsonSerializer.Deserialize<Models.Alphabet>(s) ?? new Models.Alphabet();
            }
            catch { /* try next */ }
        }
        return null;
    }

    private static IEnumerable<string> AlphabetCandidates(string code, string? script)
    {
        if (!string.IsNullOrEmpty(script))
            yield return $"alphabets/{code}-{script}.json";
        yield return $"alphabets/{code}.json";
    }

    /// <summary>Lists available keyboard layout identifiers.</summary>

    public static List<string> GetAvailableLayouts()
        => ResourceLoader.Enumerate("layouts").Select(n => n.Replace(".json", "")).OrderBy(x => x).ToList();

    /// <summary>Loads a keyboard layout by identifier.</summary>
    /// <param name="layoutId">Layout identifier, e.g. "en-us".</param>
    /// <exception cref="ArgumentException">If the layout is not found.</exception>

    public static KeyboardLayout LoadKeyboard(string layoutId)
    {
        using var s = ResourceLoader.Open($"layouts/{layoutId}.json");
        if (s == null) throw new ArgumentException($"Keyboard layout '{layoutId}' not found.");
        return JsonSerializer.Deserialize<KeyboardLayout>(s) ?? new KeyboardLayout();
    }

    // Diacritic utilities: expose via facade
    /// <summary>Returns text with diacritic marks removed.</summary>
    public static string StripDiacritics(string s) => Diacritics.DiacriticUtils.StripDiacritics(s);
    /// <summary>Returns true if the string contains diacritic marks.</summary>
    public static bool HasDiacritics(string s) => Diacritics.DiacriticUtils.HasDiacritics(s);

    /// <summary>Returns a map of base letter to diacritic variants for the language.</summary>
    /// <param name="code">Language code, e.g. "pl".</param>
    /// <param name="script">Optional script for the language.</param>
    public static Dictionary<string, List<string>> GetDiacriticVariants(string code, string? script = null)
    {
        var data = TryGetAlphabet(code, script);
        if (data == null) throw new FileNotFoundException($"Alphabet data for code '{code}' not found");
        var upper = data.Uppercase ?? new List<string>();
        var lower = data.Lowercase ?? new List<string>();
        var variants = Diacritics.DiacriticUtils.DiacriticVariants(upper).ToDictionary(k => k.Key, v => v.Value);
        foreach (var kv in Diacritics.DiacriticUtils.DiacriticVariants(lower))
            variants[kv.Key] = kv.Value;
        return variants;
    }

    // Language detection
    /// <summary>
    /// Detects likely languages using character-based scoring. Candidates must be provided.
    /// </summary>
    public static List<(string lang, double score)> DetectLanguages(string text, IEnumerable<string> candidateLangs, IDictionary<string, double>? priors = null, int topk = 3)
        => Detection.Detector.DetectLanguages(text, candidateLangs, priors, topk);

    /// <summary>
    /// Optimized detection that can auto-select candidates when <c>null</c> is passed.
    /// </summary>
    public static List<(string lang, double score)> OptimizedDetectLanguages(string text, IEnumerable<string>? candidateLangs = null, IDictionary<string, double>? priors = null, int topk = 3)
        => Detection.Detector.OptimizedDetectLanguages(text, candidateLangs, priors, topk);
}

