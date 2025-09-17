using WA = WorldAlphabets.WorldAlphabets;
using Xunit;

namespace WorldAlphabets.Tests;

public class DiacriticsTests
{
    [Fact]
    public void StripDiacritics_Works()
    {
        Assert.Equal("cafe", WA.StripDiacritics("café"));
        Assert.True(WA.HasDiacritics("é"));
    }
}

