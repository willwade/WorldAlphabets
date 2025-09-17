using WA = WorldAlphabets.WorldAlphabets;
using Xunit;

namespace WorldAlphabets.Tests;

public class DetectionTests
{
    [Fact]
    public void DetectLanguages_ManualCandidates_Works()
    {
        var res = WA.DetectLanguages("Hello world", new []{"en","fr","de"});
        Assert.NotEmpty(res);
        Assert.Equal(3, res.Count);
        Assert.Equal("en", res[0].lang);
    }

    [Fact]
    public void OptimizedDetectLanguages_NoCandidates_Works()
    {
        var res = WA.OptimizedDetectLanguages("Bonjour comment allez-vous?");
        Assert.NotEmpty(res);
    }
}

