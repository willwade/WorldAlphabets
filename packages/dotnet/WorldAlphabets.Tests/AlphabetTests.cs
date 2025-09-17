using WA = WorldAlphabets.WorldAlphabets;
using Xunit;

namespace WorldAlphabets.Tests;

public class AlphabetTests
{
    [Fact]
    public void LoadAlphabet_English_HasUppercase()
    {
        var alphabet = WA.LoadAlphabet("en", "Latn");
        Assert.Contains("A", alphabet.Uppercase);
        Assert.Contains("e", alphabet.Frequency.Keys);
    }

    [Fact]
    public void GetScripts_Serbian_ReturnsBoth()
    {
        var scripts = WA.GetScripts("sr");
        Assert.Contains("Cyrl", scripts);
        Assert.Contains("Latn", scripts);
    }
}

