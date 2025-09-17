#if NETSTANDARD2_0
namespace System.Runtime.CompilerServices
{
    // Shim for init-only setters support on netstandard2.0
    internal sealed class IsExternalInit { }
}
#endif

