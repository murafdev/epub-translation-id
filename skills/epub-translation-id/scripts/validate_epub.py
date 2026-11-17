#!/usr/bin/env python3
"""Validate a translated EPUB against its source.

Usage:
    python3 validate_epub.py SOURCE.epub OUTPUT.epub WORKDIR

Checks include ZIP/mimetype integrity, XML parsing, OPF manifest/spine,
SHA-256 identity of every image, internal links, image counts and positions,
paragraph alignment, and suspicious untranslated English paragraphs.
"""
import sys, os, re, json, html, hashlib, zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import unquote

NS = {
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
}
IMG_EXT = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')
BLOCKS = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
ENG = set(
    'the and that with from this have will your you not are was were for but '
    'what would could should there their they them then than when where which '
    'while who whom whose why how all any both each few more most other some '
    'such only own same so too very can just now into over after before about '
    'under again further once here because until during above below between '
    'through without within along across behind beyond upon against among around'.split())


class SectionParser(HTMLParser):
    """Count text paragraphs and record the text index of each <img>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.buf = []
        self.text_count = 0
        self.images = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in BLOCKS:
            if self.depth == 0:
                self.buf = []
            self.depth += 1
        elif tag == 'img':
            self.images.append(self.text_count)

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == 'img':
            self.images.append(self.text_count)
        else:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.depth > 0:
            self.buf.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in BLOCKS and self.depth > 0:
            text = ' '.join(''.join(self.buf).split())
            if text:
                self.text_count += 1
            self.depth -= 1
            self.buf = []


def body_blocks(raw):
    """Return visible text blocks from the body, excluding head/scripts."""
    raw = re.sub(r'<head\b.*?</head>', ' ', raw, flags=re.S | re.I)
    raw = re.sub(r'<(script|style)\b.*?</\1>', ' ', raw, flags=re.S | re.I)
    raw = re.sub(r'</(?:p|h[1-6]|li|div|td|tr|blockquote)>', '\n', raw, flags=re.I)
    raw = re.sub(r'<br\s*/?>', ' ', raw, flags=re.I)
    text = html.unescape(re.sub(r'<[^>]+>', ' ', raw)).replace('\xa0', ' ')
    for line in text.splitlines():
        line = ' '.join(line.split())
        if line:
            yield line


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    source, output, work = sys.argv[1], sys.argv[2], sys.argv[3]
    z = zipfile.ZipFile(output)
    o = zipfile.ZipFile(source)
    issues = []
    report = []

    # ZIP and mimetype
    bad_zip = z.testzip()
    if bad_zip:
        issues.append(f'ZIP corrupt: {bad_zip}')
    names = z.namelist()
    if not names or names[0] != 'mimetype':
        issues.append('mimetype is not first entry')
    elif z.getinfo('mimetype').compress_type != zipfile.ZIP_STORED:
        issues.append('mimetype is compressed')
    if 'mimetype' in names and z.read('mimetype') != b'application/epub+zip':
        issues.append('mimetype content wrong')

    # XML parse
    for n in names:
        if n.endswith(('.html', '.xhtml', '.opf', '.ncx', '.xml')):
            try:
                ET.fromstring(z.read(n))
            except Exception as e:
                issues.append(f'XML parse error {n}: {e}')

    # OPF metadata, manifest and spine
    opf_name = next((n for n in names if n.endswith('.opf')), None)
    if not opf_name:
        issues.append('OPF not found')
    else:
        opf = ET.fromstring(z.read(opf_name))
        lang = opf.find('.//dc:language', NS)
        if lang is None or lang.text != 'id':
            issues.append('dc:language is not id')
        base = os.path.dirname(opf_name)
        manifest = {
            item.get('id'): item.get('href')
            for item in opf.findall('.//opf:manifest/opf:item', NS)
        }
        for idref in [i.get('idref') for i in opf.findall('.//opf:spine/opf:itemref', NS)]:
            if idref not in manifest:
                issues.append(f'spine idref missing from manifest: {idref}')
        for href in manifest.values():
            target = os.path.normpath(
                os.path.join(base, unquote(href))).replace('\\', '/')
            if target not in names:
                issues.append(f'manifest item missing from archive: {href}')

    # Images: compare every image file in the archive by SHA-256.
    def imgs(zz):
        return {n: hashlib.sha256(zz.read(n)).hexdigest()
                for n in zz.namelist() if n.lower().endswith(IMG_EXT)}
    a, b = imgs(o), imgs(z)
    if set(a) != set(b):
        issues.append(f'image file set differs: missing={sorted(set(a)-set(b))}, '
                      f'extra={sorted(set(b)-set(a))}')
    for n in sorted(set(a) & set(b)):
        if a[n] != b[n]:
            issues.append(f'image changed: {n}')
    report.append(f'images: {len(b)}; identical to source: {a == b}')

    # Internal links and image references
    names_set = set(names)
    for n in names:
        if n.endswith(('.html', '.xhtml')):
            t = z.read(n).decode('utf-8', 'ignore')
            for m in re.finditer(r'(?:src|href)="([^"#]+)(?:#[^"]*)?"', t):
                target = os.path.normpath(
                    os.path.join(os.path.dirname(n), unquote(m.group(1)))).replace('\\', '/')
                if target not in names_set and not m.group(1).startswith(
                        ('http', 'mailto', 'data:', 'tel:')):
                    issues.append(f'broken link {n}: {m.group(1)}')

    # Image counts and positions per translated section.
    meta = json.load(open(os.path.join(work, 'meta.json'), encoding='utf-8'))
    positions_checked = 0
    for section in meta['sections']:
        n = section['file']
        if n not in names_set:
            continue
        t = z.read(n).decode('utf-8', 'ignore')
        count = len(re.findall(r'<img\b', t, re.I))
        expected = len(section.get('images', []))
        if count != expected:
            issues.append(f'{n}: img count {count}, expected {expected}')

        parser = SectionParser()
        parser.feed(t)
        expected_pos = [int(im['index']) for im in section.get('images', [])]
        if parser.images != expected_pos:
            issues.append(f'{n}: img positions {parser.images}, expected {expected_pos}')
        positions_checked += len(expected_pos)

        # The builder must remove legacy height="100%" sizing.
        for m in re.finditer(r'<img\b[^>]*>', t, re.I):
            tag = m.group(0)
            if re.search(r'height\s*=\s*["\']?100%', tag, re.I) or \
               re.search(r'height\s*:\s*100%', tag, re.I):
                issues.append(f'{n}: image still uses height:100%')

    # Paragraph counts: src, id, and meta must agree.
    for section in meta['sections']:
        sid = section['id']
        id_path = os.path.join(work, 'id', f'section-{sid}.txt')
        src_path = os.path.join(work, 'src', f'section-{sid}.txt')
        if not os.path.exists(id_path):
            continue
        id_lines = [l for l in open(id_path, encoding='utf-8') if l.strip()]
        if len(id_lines) != section['paragraphs']:
            issues.append(f'section {sid}: id has {len(id_lines)} lines, '
                          f'expected {section["paragraphs"]}')
        if os.path.exists(src_path):
            src_lines = [l for l in open(src_path, encoding='utf-8') if l.strip()]
            if len(src_lines) != len(id_lines):
                issues.append(f'section {sid}: src {len(src_lines)} lines, '
                              f'id {len(id_lines)} lines')

    # English function words, checked per visible paragraph.
    english_hits = []
    for n in names:
        if not n.endswith(('.html', '.xhtml')):
            continue
        t = z.read(n).decode('utf-8', 'ignore')
        for block in body_blocks(t):
            ws = re.findall(r"[A-Za-z][A-Za-z'’-]+", block.lower())
            if len(ws) < 10:
                continue
            ratio = sum(1 for w in ws if w in ENG) / len(ws)
            if ratio > 0.15:
                english_hits.append((n, ratio, block[:160]))
    if english_hits:
        issues.append(f'possible untranslated English paragraphs: {len(english_hits)}')
        for n, ratio, preview in english_hits[:12]:
            issues.append(f'  {n} ({ratio:.0%}): {preview}')

    # Report
    report.append(f'entries: {len(names)}')
    report.append(f'image tags: {sum(len(re.findall(rb"<img", z.read(n))) for n in names if n.endswith((".html", ".xhtml")))}')
    report.append(f'image positions checked: {positions_checked}')
    report.append(f'English-suspect paragraphs: {len(english_hits)}')
    report.append(f'issues: {len(issues)}')
    for i in issues:
        report.append(' - ' + i)

    text = '\n'.join(report)
    open(os.path.join(work, 'validation.txt'), 'w', encoding='utf-8').write(text + '\n')
    print(text)
    if issues:
        sys.exit(2)


if __name__ == '__main__':
    main()
