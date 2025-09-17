using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace WorldAlphabets.Models;

/// <summary>
/// Legends shown on a key across modifier layers (base, shift, caps, AltGr...).
/// </summary>
public sealed class LayerLegends
{
    /// <summary>Legend on the unmodified (base) layer.</summary>
    [JsonPropertyName("base")] public string? Base { get; init; }
    /// <summary>Legend when Shift is active.</summary>
    [JsonPropertyName("shift")] public string? Shift { get; init; }
    /// <summary>Legend when Caps Lock is active.</summary>
    [JsonPropertyName("caps")] public string? Caps { get; init; }
    /// <summary>Legend when AltGr is active.</summary>
    [JsonPropertyName("altgr")] public string? AltGr { get; init; }
    /// <summary>Legend when Shift+AltGr is active.</summary>
    [JsonPropertyName("shift_altgr")] public string? ShiftAltGr { get; init; }
    /// <summary>Legend when Ctrl is active.</summary>
    [JsonPropertyName("ctrl")] public string? Ctrl { get; init; }
    /// <summary>Legend when Alt is active.</summary>
    [JsonPropertyName("alt")] public string? Alt { get; init; }
}

/// <summary>
/// A single key in the layout, with position, shape, virtual/scan codes and legends.
/// </summary>
public sealed class KeyEntry
{
    /// <summary>Position identifier (e.g. "AE01").</summary>
    [JsonPropertyName("pos")] public string? Pos { get; init; }
    /// <summary>Row index for the key.</summary>
    [JsonPropertyName("row")] public int? Row { get; init; }
    /// <summary>Column index for the key.</summary>
    [JsonPropertyName("col")] public int? Col { get; init; }
    /// <summary>Optional shape metrics for rendering.</summary>
    [JsonPropertyName("shape")] public Dictionary<string, double>? Shape { get; init; }
    /// <summary>Virtual key code identifier.</summary>
    [JsonPropertyName("vk")] public string? Vk { get; init; }
    /// <summary>Scan code identifier.</summary>
    [JsonPropertyName("sc")] public string? Sc { get; init; }
    /// <summary>Legends for the various modifier layers.</summary>
    [JsonPropertyName("legends")] public LayerLegends Legends { get; init; } = new();
    /// <summary>True if this is a dead key (combines with next key).</summary>
    [JsonPropertyName("dead")] public bool Dead { get; init; }
    /// <summary>Optional notes for this key.</summary>
    [JsonPropertyName("notes")] public List<string> Notes { get; init; } = new();
}

/// <summary>
/// Dead key definition: trigger and composition map for resulting characters.
/// </summary>
public sealed class DeadKey
{
    /// <summary>Display name of the dead key.</summary>
    [JsonPropertyName("name")] public string? Name { get; init; }
    /// <summary>Character that acts as the dead key trigger.</summary>
    [JsonPropertyName("trigger")] public string Trigger { get; init; } = string.Empty;
    /// <summary>Composition mapping: next key -> composed output.</summary>
    [JsonPropertyName("compose")] public Dictionary<string, string> Compose { get; init; } = new();
}

/// <summary>
/// Multi-key ligature mapping.
/// </summary>
public sealed class Ligature
{
    /// <summary>Keys to press in sequence.</summary>
    [JsonPropertyName("keys")] public List<string> Keys { get; init; } = new();
    /// <summary>Resulting output string.</summary>
    [JsonPropertyName("output")] public string Output { get; init; } = string.Empty;
}

/// <summary>
/// Keyboard layout definition including keys, dead keys, ligatures and metadata.
/// </summary>
public sealed class KeyboardLayout
{
    /// <summary>Stable layout identifier (e.g. "en-us").</summary>
    [JsonPropertyName("id")] public string Id { get; init; } = string.Empty;
    /// <summary>Human-readable layout name.</summary>
    [JsonPropertyName("name")] public string Name { get; init; } = string.Empty;
    /// <summary>Source or origin of the layout data.</summary>
    [JsonPropertyName("source")] public string Source { get; init; } = string.Empty;
    /// <summary>Optional ISO variant string.</summary>
    [JsonPropertyName("iso_variant")] public string? IsoVariant { get; init; }
    /// <summary>Arbitrary feature flags.</summary>
    [JsonPropertyName("flags")] public Dictionary<string, bool> Flags { get; init; } = new();
    /// <summary>All key entries for the layout.</summary>
    [JsonPropertyName("keys")] public List<KeyEntry> Keys { get; init; } = new();
    /// <summary>Optional list of dead keys.</summary>
    [JsonPropertyName("dead_keys")] public List<DeadKey>? DeadKeys { get; init; }
    /// <summary>Optional list of ligatures.</summary>
    [JsonPropertyName("ligatures")] public List<Ligature>? Ligatures { get; init; }
    /// <summary>Additional metadata.</summary>
    [JsonPropertyName("meta")] public Dictionary<string, object> Meta { get; init; } = new();
}

