using System.Text.Json.Serialization;

namespace WorldAlphabets.Models;

/// <summary>
/// Metadata entry describing a language and its available scripts in the index.
/// </summary>
public sealed class IndexEntry
{
    /// <summary>BCP-47 language code (e.g. "en", "sr").</summary>
    [JsonPropertyName("language")] public string Language { get; init; } = string.Empty;

    /// <summary>Primary script for this entry (e.g. "Latn").</summary>
    [JsonPropertyName("script")] public string? Script { get; init; }

    /// <summary>All scripts available for this language.</summary>
    [JsonPropertyName("scripts")] public string[]? Scripts { get; init; }

    /// <summary>Human-readable language name, if provided.</summary>
    [JsonPropertyName("name")] public string? Name { get; init; }

    /// <summary>ISO 639-1 language code (2-letter), if available.</summary>
    [JsonPropertyName("iso639_1")] public string? Iso6391 { get; init; }

    /// <summary>ISO 639-3 language code (3-letter), if available.</summary>
    [JsonPropertyName("iso639_3")] public string? Iso6393 { get; init; }

    /// <summary>Relative path/filename of the alphabet JSON for this entry.</summary>
    [JsonPropertyName("file")] public string? File { get; init; }

    /// <summary>Total letter count for this alphabet (if present).</summary>
    [JsonPropertyName("letterCount")] public int? LetterCount { get; init; }
}

