using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace WorldAlphabets.Models;

/// <summary>
/// Alphabet data for a specific language and script: letters, frequency, and metadata.
/// </summary>
public sealed class Alphabet
{
    /// <summary>Letters in nominal alphabetical order for the language/script.</summary>
    [JsonPropertyName("alphabetical")]
    public List<string> Alphabetical { get; init; } = new();

    /// <summary>Uppercase letters used in this alphabet.</summary>
    [JsonPropertyName("uppercase")]
    public List<string> Uppercase { get; init; } = new();

    /// <summary>Lowercase letters used in this alphabet.</summary>
    [JsonPropertyName("lowercase")]
    public List<string> Lowercase { get; init; } = new();

    /// <summary>Relative frequency for letters (0..1) keyed by lowercase letter.</summary>
    [JsonPropertyName("frequency")]
    public Dictionary<string, double> Frequency { get; init; } = new();

    /// <summary>Optional digits used in this writing system.</summary>
    [JsonPropertyName("digits")]
    public List<string>? Digits { get; init; }

    /// <summary>Script identifier (e.g. "Latn", "Cyrl") if present.</summary>
    [JsonPropertyName("script")]
    public string? Script { get; init; }

    /// <summary>Human-readable language name (e.g. "English").</summary>
    [JsonPropertyName("language")]
    public string? LanguageName { get; init; }

    /// <summary>ISO 639-1 language code (2-letter) when available.</summary>
    [JsonPropertyName("iso639_1")]
    public string? Iso6391 { get; init; }

    /// <summary>ISO 639-3 language code (3-letter) when available.</summary>
    [JsonPropertyName("iso639_3")]
    public string? Iso6393 { get; init; }
}

