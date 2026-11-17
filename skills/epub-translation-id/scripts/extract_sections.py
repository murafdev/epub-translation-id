#!/usr/bin/env python3
"""Extract paragraph-aligned source text and inline image positions from an EPUB.

Usage:
    python3 extract_sections.py BOOK.epub WORKDIR

Outputs:
    WORKDIR/src/section-XXXX.txt
    WORKDIR/meta.json
    WORKDIR/image_manifest.json

Each src file contains the section title on line 1, followed by one paragraph
per line. Italic text is marked {i}...{/i}; bold text is marked {b}...{/b};
scene breaks remain ***. Inline images are recorded in meta.json with the
paragraph index used by build_epub.py.
"""
import sys, os, re, json, html, hashlib, zipfile
import xml.etree.ElementTree as ET
from urllib.parse import unquote

NS = {
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
}
IMG_EXT = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')

# Anchored so a chapter named "chapter-3-the-title.html" is not skipped.
SKIP_FILE_RE = re.compile(
    r'^(toc|tableofcontents|contents|cover|coverpage|titlepage|nav|jln|copyright)\b',
    re.I)


def clean_text(fragment):
    """Convert an HTML fragment to plain text with {i} and {b} markers."""
    # Inline styles used by Sigil/InDesign.
    fragment = re.sub(
        r'<span[^>]*font-style:\s*italic[^>]*>(.*?)</span>',
        lambda m: '\x01' + m.group(1) + '\x02',
        fragment, flags=re.S | re.I)
    # Semantic inline tags.
    fragment = re.sub(r'<(i|em)\b[^>]*>(.*?)</\1>',
                      lambda m: '\x01' + m.group(2) + '\x02',
                      fragment, flags=re.S | re.I)
    fragment = re.sub(r'<(b|strong)\b[^>]*>(.*?)</\1>',
                      lambda m: '\x03' + m.group(2) + '\x04',
                      fragment, flags=re.S | re.I)
    fragment = re.sub(r'<br\s*/?>', ' ', fragment, flags=re.I)
    fragment = re.sub(r'<[^>]+>', '', fragment)
    fragment = html.unescape(fragment).replace('\xa0', ' ')
    fragment = re.sub(r'\s+', ' ', fragment).strip()
    return (fragment.replace('\x01', '{i}').replace('\x02', '{/i}')
            .replace('\x03', '{b}').replace('\x04', '{/b}'))


def section_id(name, fallback):
    base = os.path.basename(name)
    m = re.search(r'(\d{3,4})', base)
    return m.group(1).zfill(4) if m else f'x{fallback:04d}'


def unique_id(sid, used):
    if sid not in used:
        return sid
    if sid.startswith('x'):
        n = int(sid[1:])
        while f'x{n:04d}' in used:
            n += 1
        return f'x{n:04d}'
    n = int(sid)
    while f'{n:04d}' in used:
        n += 1
    return f'{n:04d}'


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    epub, work = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(work, 'src'), exist_ok=True)

    z = zipfile.ZipFile(epub)
    opf_name = next((n for n in z.namelist() if n.endswith('.opf')), None)
    if not opf_name:
        raise SystemExit('OPF not found')

    opf = ET.fromstring(z.read(opf_name))
    base = os.path.dirname(opf_name)
    manifest = {
        item.get('id'): item.get('href')
        for item in opf.findall('.//opf:manifest/opf:item', NS)
    }
    spine = [i.get('idref') for i in opf.findall('.//opf:spine/opf:itemref', NS)]

    sections = []
    used = set()
    for idx, idref in enumerate(spine, 1):
        href = manifest.get(idref)
        if not href:
            continue
        name = os.path.normpath(os.path.join(base, unquote(href))).replace('\\', '/')
        if not name.lower().endswith(('.html', '.xhtml')):
            continue
        if SKIP_FILE_RE.match(os.path.basename(name)):
            continue
        raw = z.read(name).decode('utf-8', 'ignore')
        if '<body' not in raw:
            continue

        title_m = re.search(r'<title[^>]*>(.*?)</title>', raw, re.S | re.I)
        title = clean_text(title_m.group(1)) if title_m else os.path.basename(name)
        body = raw.split('<body', 1)[1]
        body = body.split('>', 1)[1].split('</body>', 1)[0]

        lines = []
        images = []
        for m in re.finditer(r'<(p|h[1-6])([^>]*)>(.*?)</\1>', body, re.S | re.I):
            attrs, inner = m.group(2), m.group(3)
            if '<img' in inner.lower():
                cls = re.search(r'class="([^"]*)"', attrs, re.I)
                cls_name = cls.group(1) if cls else 'P_TEXTBODY_CENTERALIGN_PAGEBREAK'
                for img in re.findall(r'<img[^>]*>', inner, re.I):
                    images.append({
                        'index': len(lines),
                        'tag': f'<p class="{cls_name}"><span>{img}</span></p>',
                    })
                # Image-only blocks are not text paragraphs. If a block mixes
                # text and an image, the text is kept and the image is anchored
                # at the paragraph index before that text.
                text = clean_text(inner)
                if text:
                    lines.append(text)
                continue
            text = clean_text(inner)
            if text:
                lines.append(text)

        if not lines:
            continue
        norm = lambda s: re.sub(r'[^a-z0-9]+', '', s.lower())
        title_removed = False
        if title and lines and norm(title) and norm(lines[0])[:20] == norm(title)[:20]:
            # The body often repeats the <title> as an <h1>. Keep only the
            # title from <title>; image indices are already in title-inclusive
            # coordinates in this case.
            lines = lines[1:]
            title_removed = True
        if not lines:
            continue

        if not title_removed:
            # The body had no title paragraph. build_epub.py still generates a
            # title heading. A leading image (index 0) stays before that
            # heading; later images shift by one to keep their text-relative
            # position in the generated section.
            for im in images:
                if im['index'] > 0:
                    im['index'] += 1

        content = [title] + lines
        sid = unique_id(section_id(name, idx), used)
        used.add(sid)
        outname = f'section-{sid}.txt'
        with open(os.path.join(work, 'src', outname), 'w', encoding='utf-8') as f:
            f.write('\n'.join(content) + '\n')
        sections.append({
            'id': sid,
            'file': name,
            'title': title,
            'paragraphs': len(content),
            'images': images,
        })
        print(f'{outname}: {len(content)} paragraf, {len(images)} gambar')

    image_manifest = {}
    for n in z.namelist():
        if n.lower().endswith(IMG_EXT):
            data = z.read(n)
            image_manifest[n] = {
                'sha256': hashlib.sha256(data).hexdigest(),
                'bytes': len(data),
            }
    with open(os.path.join(work, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump({'sections': sections, 'opf': opf_name}, f,
                  ensure_ascii=False, indent=1)
    with open(os.path.join(work, 'image_manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(image_manifest, f, ensure_ascii=False, indent=1)
    print(f'images: {len(image_manifest)}')


if __name__ == '__main__':
    main()
