using System.Text.Json.Serialization;

namespace WorldAlphabets.Models;

public sealed class IndexEntry
{
    [JsonPropertyName("language")] public string Language { get; init; } = string.Empty;
    [JsonPropertyName("script")] public string? Script { get; init; }
    [JsonPropertyName("scripts")] public string[]? Scripts { get; init; }
    [JsonPropertyName("name")] public string? Name { get; init; }
    [JsonPropertyName("iso639_1")] public string? Iso6391 { get; init; }
    [JsonPropertyName("iso639_3")] public string? Iso6393 { get; init; }
    [JsonPropertyName("file")] public string? File { get; init; }
    [JsonPropertyName("letterCount")] public int? LetterCount { get; init; }
}

