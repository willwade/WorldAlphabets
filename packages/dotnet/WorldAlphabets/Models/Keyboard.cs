using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace WorldAlphabets.Models;

public sealed class LayerLegends
{
    [JsonPropertyName("base")] public string? Base { get; init; }
    [JsonPropertyName("shift")] public string? Shift { get; init; }
    [JsonPropertyName("caps")] public string? Caps { get; init; }
    [JsonPropertyName("altgr")] public string? AltGr { get; init; }
    [JsonPropertyName("shift_altgr")] public string? ShiftAltGr { get; init; }
    [JsonPropertyName("ctrl")] public string? Ctrl { get; init; }
    [JsonPropertyName("alt")] public string? Alt { get; init; }
}

public sealed class KeyEntry
{
    [JsonPropertyName("pos")] public string? Pos { get; init; }
    [JsonPropertyName("row")] public int? Row { get; init; }
    [JsonPropertyName("col")] public int? Col { get; init; }
    [JsonPropertyName("shape")] public Dictionary<string, double>? Shape { get; init; }
    [JsonPropertyName("vk")] public string? Vk { get; init; }
    [JsonPropertyName("sc")] public string? Sc { get; init; }
    [JsonPropertyName("legends")] public LayerLegends Legends { get; init; } = new();
    [JsonPropertyName("dead")] public bool Dead { get; init; }
    [JsonPropertyName("notes")] public List<string> Notes { get; init; } = new();
}

public sealed class DeadKey
{
    [JsonPropertyName("name")] public string? Name { get; init; }
    [JsonPropertyName("trigger")] public string Trigger { get; init; } = string.Empty;
    [JsonPropertyName("compose")] public Dictionary<string, string> Compose { get; init; } = new();
}

public sealed class Ligature
{
    [JsonPropertyName("keys")] public List<string> Keys { get; init; } = new();
    [JsonPropertyName("output")] public string Output { get; init; } = string.Empty;
}

public sealed class KeyboardLayout
{
    [JsonPropertyName("id")] public string Id { get; init; } = string.Empty;
    [JsonPropertyName("name")] public string Name { get; init; } = string.Empty;
    [JsonPropertyName("source")] public string Source { get; init; } = string.Empty;
    [JsonPropertyName("iso_variant")] public string? IsoVariant { get; init; }
    [JsonPropertyName("flags")] public Dictionary<string, bool> Flags { get; init; } = new();
    [JsonPropertyName("keys")] public List<KeyEntry> Keys { get; init; } = new();
    [JsonPropertyName("dead_keys")] public List<DeadKey>? DeadKeys { get; init; }
    [JsonPropertyName("ligatures")] public List<Ligature>? Ligatures { get; init; }
    [JsonPropertyName("meta")] public Dictionary<string, object> Meta { get; init; } = new();
}

