using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;

namespace WorldAlphabets.Diacritics;

/// <summary>
/// Diacritic utilities: normalization, detection, and grouping of diacritic variants.
/// </summary>

public static class DiacriticUtils
{
    private static readonly Dictionary<char, char> SpecialBase = new()
    {
        ['Ł'] = 'L', ['ł'] = 'l',
        ['Đ'] = 'D', ['đ'] = 'd',
        ['Ø'] = 'O', ['ø'] = 'o',
        ['Ð'] = 'D', ['ð'] = 'd',
        ['Þ'] = 'T', ['þ'] = 't',
        ['Ŋ'] = 'N', ['ŋ'] = 'n'
    };

    /// <summary>Returns text with diacritic marks removed.</summary>
    public static string StripDiacritics(string? text)
    {
        if (string.IsNullOrEmpty(text)) return text ?? string.Empty;
        var sb = new StringBuilder(text.Length);
        foreach (var ch in text!)
        {
            if (SpecialBase.TryGetValue(ch, out var mapped))
            {
                sb.Append(mapped);
                continue;
            }
            var decomposed = ch.ToString().Normalize(NormalizationForm.FormD);
            foreach (var dc in decomposed)
            {
                var cat = CharUnicodeInfo.GetUnicodeCategory(dc);
                if (cat != UnicodeCategory.NonSpacingMark)
                    sb.Append(dc);
            }
        }
        return sb.ToString().Normalize(NormalizationForm.FormC);
    }

    /// <summary>True if the string contains diacritic marks.</summary>
    public static bool HasDiacritics(string? s)
        => !string.IsNullOrEmpty(s) && StripDiacritics(s!) != s;

    /// <summary>Filters the provided characters to only those with diacritics.</summary>
    public static IEnumerable<string> CharactersWithDiacritics(IEnumerable<string> chars)
        => chars.Where(c => !string.IsNullOrEmpty(c) && HasDiacritics(c!));

    /// <summary>
    /// Groups characters by their base (diacritic-stripped) form. Only groups with multiple
    /// variants are returned.
    /// </summary>
    public static Dictionary<string, List<string>> DiacriticVariants(IEnumerable<string> chars)
    {
        var groups = new Dictionary<string, HashSet<string>>();
        foreach (var ch in chars)
        {
            if (string.IsNullOrEmpty(ch)) continue;
            var baseForm = StripDiacritics(ch);
            if (!groups.TryGetValue(baseForm, out var set))
            {
                set = new HashSet<string>();
                groups[baseForm] = set;
            }
            set.Add(ch);
        }
        return groups
            .Where(kv => kv.Value.Count > 1)
            .ToDictionary(kv => kv.Key, kv => kv.Value.OrderBy(x => x).ToList());
    }
}

