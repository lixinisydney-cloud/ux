"""Export the static prototype as an offline HTML file; no third-party tools."""
import base64
import json
import html as html_module
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / 'index.html').read_text(encoding='utf-8')
html = html.replace(
    '<link rel="stylesheet" href="styles.css" />',
    '<style>\n' + (root / 'styles.css').read_text(encoding='utf-8') + '\n</style>')
bootstrap = (root / 'data/offline-bundle.js').read_text(encoding='utf-8')
real = json.loads((root / 'data/classifications.real.json').read_text(encoding='utf-8-sig'))
bootstrap += '\nglobalThis.RE_BOOTSTRAP.real=' + json.dumps(
    real, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + ';\n'
html = html.replace('<script src="data/offline-bundle.js"></script>', '<script>\n' + bootstrap + '\n</script>')
html = html.replace('<script src="classification-store.js"></script>', '<script>\n' + (
    root / 'classification-store.js').read_text(encoding='utf-8') + '\n</script>')
# These unused local reference crops are deliberately excluded from publication.
excluded = {'photo_typography', 'photo_poster'}
assets = {
    p.stem: 'data:image/webp;base64,' + base64.b64encode(p.read_bytes()).decode()
    for p in sorted((root / 'assets').glob('*.webp')) if p.stem not in excluded
}
avatar = 'data:image/svg+xml;base64,' + base64.b64encode(
    (root / 'assets/avatar.svg').read_bytes()).decode()
html = html.replace('assets/avatar.svg', avatar)
inline_pictures = {
    'assets/' + p.name: 'data:image/svg+xml;base64,' + base64.b64encode(p.read_bytes()).decode()
    for p in sorted((root / 'assets').glob('author-*.svg'))
}
html = html.replace("'use strict';", "'use strict';\nglobalThis.RE_INLINE_PICTURES=" + json.dumps(inline_pictures, separators=(',', ':')) + ';', 1)
lookup = 'const asset=cover=>`assets/${cover}.webp`;'
assert lookup in html, 'Asset lookup changed: review the export before publishing'
html = html.replace(
    lookup,
    'const INLINE_ASSETS=' + json.dumps(assets, separators=(',', ':'))
    + ';\nconst asset=cover=>INLINE_ASSETS[cover];')
credits = (root / 'docs/asset-sources-v08.json').read_text(encoding='utf-8')
notices = '\n\n'.join('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines()) for p in sorted((root / 'docs/licenses').glob('*.txt')))
html = html.replace('</body>', '<template id="assetLicenseNotices"><pre>' + html_module.escape(credits + '\n\n' + notices) + '</pre></template>\n</body>')
output = root / 'RE_FOLD_v06_Demo.html'
output.write_text(html, encoding='utf-8')
print(f'{output.name}: {len(assets)} covers embedded; local reference crops excluded')
