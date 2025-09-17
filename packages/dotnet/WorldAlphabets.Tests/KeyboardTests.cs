using WA = WorldAlphabets.WorldAlphabets;
using Xunit;

namespace WorldAlphabets.Tests;

public class KeyboardTests
{
    [Fact]
    public void GetAvailableLayouts_HasEnUs()
    {
        var layouts = WA.GetAvailableLayouts();
        Assert.Contains("en-us", layouts);
    }

    [Fact]
    public void LoadKeyboard_EnUs_HasKeys()
    {
        var kb = WA.LoadKeyboard("en-us");
        Assert.NotEmpty(kb.Keys);
    }
}

