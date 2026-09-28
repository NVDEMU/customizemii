from pathlib import Path
import re, sys

root = Path(sys.argv[1])

for path in root.rglob('*.cs'):
    text = path.read_text(encoding='utf-8-sig')
    text = text.replace('using System.Windows.Forms;', 'using Majorsilence.Forms;')
    text = text.replace('System.Windows.Forms.', 'Majorsilence.Forms.')
    text = text.replace('using System.Drawing;', 'using Majorsilence.Forms.Drawing;')
    text = text.replace('System.Drawing.Drawing2D.', 'Majorsilence.Forms.Drawing.Drawing2D.')
    text = text.replace('System.Drawing.Imaging.', 'Majorsilence.Forms.Drawing.Imaging.')
    text = text.replace('System.Drawing.Text.', 'Majorsilence.Forms.Drawing.Text.')
    text = text.replace('Application.StartupPath', 'AppContext.BaseDirectory')
    path.write_text(text, encoding='utf-8')

(root / 'CustomizeMii' / 'CustomizeMii_zlib.cs').write_text('''using System.IO;\nusing System.IO.Compression;\n\nnamespace TransmitMii\n{\n    public static class zlib\n    {\n        public static byte[] Compress(byte[] inFile)\n        {\n            using var output = new MemoryStream();\n            using (var zlib = new ZLibStream(output, CompressionLevel.Optimal, leaveOpen: true))\n            {\n                zlib.Write(inFile, 0, inFile.Length);\n            }\n            return output.ToArray();\n        }\n    }\n}\n''', encoding='utf-8')

gx = root / 'ForwardMii' / 'ForwardMii_GX.cs'
text = gx.read_text(encoding='utf-8-sig')
start = text.find('        [DllImport("kernel32.dll"')
if start != -1:
    method_start = text.find('        public static string GetShortPathName', start)
    method_end = text.find('        private bool Compile()', method_start)
    replacement = '''        public static string GetShortPathName(string longPath)
    {
        if (!OperatingSystem.IsWindows()) return Path.GetFullPath(longPath);
        uint size = 256;
        StringBuilder buffer = new StringBuilder((int)size);
        uint result = GetShortPathNameNative(longPath, buffer, size);
        return result == 0 ? longPath : buffer.ToString();
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    static extern uint GetShortPathNameNative([MarshalAs(UnmanagedType.LPTStr)] string lpszLongPath,
                                               [MarshalAs(UnmanagedType.LPTStr)] StringBuilder lpszShortPath,
                                               uint cchBuffer);

'''.replace("\n", "\n        ")
    text = text[:start] + replacement + text[method_end:]
    gx.write_text(text, encoding='utf-8')

(root / 'CustomizeMii' / 'lControlsCompat.cs').write_text('''using Majorsilence.Forms;\nnamespace lControls\n{\n    public sealed class CheckLED : CheckBox\n    {\n        public enum LEDColor { Green, Red, Yellow }\n        public LEDColor LedColor { get; set; }\n    }\n}\n''', encoding='utf-8')

for csproj in root.rglob('*.csproj'):
    text = csproj.read_text(encoding='utf-8-sig')
    text = re.sub(r'\s*<Reference Include="lControls"[^>]*>.*?</Reference>', '', text, flags=re.S)
    text = re.sub(r'<TargetFrameworkVersion>.*?</TargetFrameworkVersion>', '<TargetFramework>net10.0</TargetFramework>', text)
    text = re.sub(r'<Import Project="[^"]*Microsoft\.CSharp\.targets"\s*/>', '', text)
    if csproj.name == 'CustomizeMii.csproj' and 'lControlsCompat.cs' not in text:
        text = text.replace('  <ItemGroup>', '  <ItemGroup>\n    <Compile Include="lControlsCompat.cs" />', 1)
    if 'Majorsilence.Forms.Avalonia' not in text:
        text = text.replace('  <ItemGroup>', '  <ItemGroup>\n    <PackageReference Include="Majorsilence.Forms" Version="26.0.30" />\n    <PackageReference Include="Majorsilence.Forms.Avalonia" Version="26.0.30" />', 1)
    if 'Majorsilence.Forms.Drawing.Common' not in text:
        text = text.replace('</Project>', '  <ItemGroup>\n    <PackageReference Include="Majorsilence.Forms.Drawing.Common" Version="26.0.30" />\n  </ItemGroup>\n</Project>')
    csproj.write_text(text, encoding='utf-8')

customize = root / 'CustomizeMii' / 'CustomizeMii.csproj'
text = customize.read_text(encoding='utf-8-sig')
text = re.sub(r'\s*<ProjectReference Include="\.\\CustomizeMiiInstaller\\CustomizeMiiInstaller\.csproj">.*?</ProjectReference>', '', text, flags=re.S)
text = re.sub(r'\s*<ProjectReference Include="\.\\ForwardMii\\ForwardMii\.csproj">.*?</ProjectReference>', '', text, flags=re.S)
if 'Link="ForwardMii\\ForwardMii_GX.cs"' not in text:
    items = []
    for p in sorted((root / 'ForwardMii').glob('*.cs')):
        if p.name != 'AssemblyInfo.cs': items.append(f'    <Compile Include="..\\ForwardMii\\{p.name}" Link="ForwardMii\\{p.name}" />')
    text = text.replace('  <ItemGroup>', '  <ItemGroup>\n' + '\n'.join(items), 1)
customize.write_text(text, encoding='utf-8')