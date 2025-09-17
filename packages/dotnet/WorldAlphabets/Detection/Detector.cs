using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using WorldAlphabets.Models;
using WorldAlphabets.Utils;

namespace WorldAlphabets.Detection;

/// <summary>
/// Language detector based on character coverage and frequency overlap.
/// Provides optimized candidate selection and simple scoring.
/// </summary>

public static class Detector
{
    /// <summary>Weight applied to user-provided priors in the final score.</summary>
    public const double PRIOR_WEIGHT = 0.65;
    /// <summary>Weight applied to character-based score in the final score.</summary>
    public const double CHAR_WEIGHT = 0.20;

    private static IReadOnlyList<IndexEntry>? _index;
    private static IReadOnlyDictionary<string, HashSet<string>>? _charToLangs;

    private static IReadOnlyList<IndexEntry> Index => _index ??= LoadIndex();

    private static IReadOnlyList<IndexEntry> LoadIndex()
    {
        var json = ResourceLoader.ReadText("index.json");
        var entries = JsonSerializer.Deserialize<List<IndexEntry>>(json) ?? new();
        return entries;
    }

    private static void EnsureCharIndex()
    {
        if (_charToLangs != null) return;
        try
        {
            using var s = ResourceLoader.Open("char_index.json");
            if (s == null) { _charToLangs = new Dictionary<string, HashSet<string>>(); return; }
            using var doc = JsonDocument.Parse(s);
            var map = new Dictionary<string, HashSet<string>>();
            if (doc.RootElement.TryGetProperty("char_to_languages", out var c2l))
            {
                foreach (var prop in c2l.EnumerateObject())
                {
                    var set = new HashSet<string>(prop.Value.EnumerateArray().Select(e => e.GetString()!).Where(v => v!=null));
                    map[prop.Name] = set;
                }
            }
            _charToLangs = map;
        }
        catch
        {
            _charToLangs = new Dictionary<string, HashSet<string>>();
        }
    }

    /// <summary>
    /// Optimized language detection. When <c>candidateLangs</c> is null, candidates
    /// are auto-selected from character evidence in the text.
    /// </summary>
    public static List<(string lang, double score)> OptimizedDetectLanguages(string text, IEnumerable<string>? candidateLangs = null, IDictionary<string, double>? priors = null, int topk = 3)
    {
        priors ??= new Dictionary<string, double>();
        EnsureCharIndex();
        var all = candidateLangs?.ToList() ?? Index.Select(e => e.Language).Distinct().ToList();

        // Filter candidates by characters present in text
        var textChars = TokenizeCharacters(text);
        if (_charToLangs != null && _charToLangs.Count > 0)
        {
            var set = new HashSet<string>();
            foreach (var ch in textChars)
            {
                if (_charToLangs.TryGetValue(ch, out var langs))
                {
                    foreach (var l in langs) set.Add(l);
                }
            }
            if (set.Count > 0)
            {
                all = all.Where(l => set.Contains(l)).ToList();
            }
        }

        // Score using character overlap against alphabet data
        var results = new List<(string, double)>();
        foreach (var lang in all)
        {
            var alphabet = WorldAlphabets.TryGetAlphabet(lang);
            if (alphabet == null) continue;
            var alphabetChars = new HashSet<string>(alphabet.Lowercase);
            var charOverlap = CharacterOverlap(textChars, alphabetChars);
            var freqOverlap = FrequencyOverlap(textChars, alphabet.Frequency);
            var charScore = charOverlap * 0.6 + freqOverlap * 0.4;
            var prior = priors != null && priors.TryGetValue(lang, out var p) ? p : 0.0;
            var finalScore = PRIOR_WEIGHT * prior + CHAR_WEIGHT * charScore * 0.5;
            if (finalScore > 0.04)
                results.Add((lang, finalScore));
        }

        return results.OrderByDescending(t => t.Item2).Take(topk).ToList();
    }

    /// <summary>
    /// Detects likely languages using character-based scoring. Requires explicit candidates.
    /// </summary>
    public static List<(string lang, double score)> DetectLanguages(string text, IEnumerable<string> candidateLangs, IDictionary<string, double>? priors = null, int topk = 3)
    {
        // For now, reuse character-based scoring; word-rank detection can be added later.
        return OptimizedDetectLanguages(text, candidateLangs, priors, topk);
    }

    private static HashSet<string> TokenizeCharacters(string text)
    {
        var norm = text.Normalize(NormalizationForm.FormKC).ToLowerInvariant();
        return new HashSet<string>(norm.Where(char.IsLetter).Select(c => c.ToString()));
    }

    private static double CharacterOverlap(HashSet<string> textChars, HashSet<string> alphabetChars)
    {
        if (textChars.Count == 0 || alphabetChars.Count == 0) return 0.0;
        var matching = textChars.Intersect(alphabetChars).Count();
        var nonMatching = textChars.Except(alphabetChars).Count();
        if (matching == 0) return 0.0;
        var coverage = (double)matching / textChars.Count;
        var penalty = (double)nonMatching / textChars.Count;
        var alphabetCoverage = (double)matching / alphabetChars.Count;
        var score = coverage * 0.6 - penalty * 0.2 + alphabetCoverage * 0.2;
        return Math.Max(0.0, score);
    }

    private static double FrequencyOverlap(HashSet<string> textChars, IDictionary<string, double> freq)
    {
        if (textChars.Count == 0 || freq.Count == 0) return 0.0;
        double score = 0.0, total = 0.0;
        foreach (var ch in textChars)
        {
            if (freq.TryGetValue(ch, out var f) && f > 0)
            {
                score += f; total += f;
            }
        }
        return total > 0 ? score / Math.Max(total, 0.001) : 0.0;
    }
}

