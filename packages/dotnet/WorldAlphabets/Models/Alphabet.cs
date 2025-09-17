using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace WorldAlphabets.Models;

public sealed class Alphabet
{
    [JsonPropertyName("alphabetical")] public List<string> Alphabetical { get; init; } = new();
    [JsonPropertyName("uppercase")] public List<string> Uppercase { get; init; } = new();
    [JsonPropertyName("lowercase")] public List<string> Lowercase { get; init; } = new();
    [JsonPropertyName("frequency")] public Dictionary<string, double> Frequency { get; init; } = new();
    [JsonPropertyName("digits")] public List<string>? Digits { get; init; }
    [JsonPropertyName("script")] public string? Script { get; init; }
    [JsonPropertyName("language")] public string? LanguageName { get; init; }
    [JsonPropertyName("iso639_1")] public string? Iso6391 { get; init; }
    [JsonPropertyName("iso639_3")] public string? Iso6393 { get; init; }
}

