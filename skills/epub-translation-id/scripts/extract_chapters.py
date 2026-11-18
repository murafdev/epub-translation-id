#!/usr/bin/env python3
"""Extract translated chapters from an EPUB into one TXT file per chapter.

Usage:
    python3 extract_chapters.py OUTPUT.epub CHAPTERS_DIR
    python3 extract_chapters.py OUTPUT.epub WORKDIR CHAPTERS_DIR

Options:
    --wpm N          TTS speaking rate in words per minute (default: 140)
    --no-duration    Do not add estimated TTS duration to daftar-isi.txt

If WORKDIR is given, meta.json from extract_sections.py is used for section
order, and only sections with id/section-XXXX.txt are extracted.

Output:
    CHAPTERS_DIR/bab-01.txt, selingan-01.txt, ... (or slugged titles)
    CHAPTERS_DIR/daftar-isi.txt
"""
import sys, os, re, json, html, zipfile, argparse
import xml.etree.ElementTree as ET
from urllib.parse import unquote

NS = {
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

# Pages that are not story chapters and must not become chapter TXT files.
AUX_RE = re.compile(
    r'^(table of contents|daftar isi|contents|cover|sampul|title page|'
    r'halaman judul|copyright|hak cipta|about the author|tentang penulis|'
    r'newsletter|buletin|color inserts|sisipan berwarna|'
    r'character design|konsep desain|jln|iklan)\b',
    re.I)
CHAPTER_RE = re.compile(r'^(?:chapter|bab)\s+(\d+)\b', re.I)
INTERLUDE_RE = re.compile(r'^(?:interlude|selingan|side story|extra)\b', re.I)
DEFAULT_WPM = 140


def clean(fragment):
    fragment = re.sub(r'<br\s*/?>', ' ', fragment, flags=re.I)
    fragment = re.sub(r'<[^>]+>', '', fragment)
    fragment = html.unescape(fragment).replace('\xa0', ' ')
    return ' '.join(fragment.split())


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def slug(title):
    s = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    return (s[:60].rstrip('-') or 'chapter')


def format_duration(seconds):
    """Format a duration in Indonesian, e.g. '1 jam 2 menit 3 detik'."""
    seconds = int(round(seconds))
    if seconds < 60:
        return f'{seconds} detik'
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        out = f'{minutes} menit'
        return out + (f' {sec} detik' if sec else '')
    hours, minutes = divmod(minutes, 60)
    out = f'{hours} jam'
    if minutes:
        out += f' {minutes} menit'
    if sec:
        out += f' {sec} detik'
    return out


def format_duration_short(seconds):
    """Compact duration for the index table."""
    seconds = int(round(seconds))
    if seconds < 60:
        return f'{seconds} dtk'
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f'{minutes} mnt' + (f' {sec} dtk' if sec else '')
    hours, minutes = divmod(minutes, 60)
    return f'{hours} j' + (f' {minutes} mnt' if minutes else '')


def read_epub(path):
    z = zipfile.ZipFile(path)
    opf_name = next((n for n in z.namelist() if n.endswith('.opf')), None)
    if not opf_name:
        raise SystemExit('OPF not found in EPUB')
    opf = ET.fromstring(z.read(opf_name))
    base = os.path.dirname(opf_name)
    manifest = {
        item.get('id'): item.get('href')
        for item in opf.findall('.//opf:manifest/opf:item', NS)
    }
    spine = [
        item.get('idref')
        for item in opf.findall('.//opf:spine/opf:itemref', NS)
    ]
    files = []
    for idref in spine:
        href = manifest.get(idref)
        if not href:
            continue
        name = os.path.normpath(os.path.join(base, unquote(href))).replace('\\', '/')
        if name.lower().endswith(('.html', '.xhtml')):
            files.append(name)
    return z, files


def section_texts(z, name):
    raw = z.read(name).decode('utf-8', 'ignore')
    tm = re.search(r'<title[^>]*>(.*?)</title>', raw, re.S | re.I)
    title = clean(tm.group(1)) if tm else os.path.basename(name)
    body = raw.split('<body', 1)[1]
    body = body.split('>', 1)[1].split('</body>', 1)[0]
    paras = []
    for m in re.finditer(r'<(p|h[1-6])\b([^>]*)>(.*?)</\1>', body, re.S | re.I):
        inner = m.group(3)
        if '<img' in inner.lower():
            continue
        text = clean(inner)
        if not text:
            continue
        paras.append(text)
    # The builder writes the chapter title as the first paragraph. Drop it so
    # the TXT file does not repeat the title immediately after the heading.
    if paras and norm(title) and norm(paras[0])[:30] == norm(title)[:30]:
        paras = paras[1:]
    return title, paras


def main():
    parser = argparse.ArgumentParser(
        description='Extract translated chapters from an EPUB into TXT files.')
    parser.add_argument('epub', help='translated EPUB file')
    parser.add_argument(
        'paths', nargs='+', metavar='WORKDIR_OR_CHAPTERS_DIR',
        help='CHAPTERS_DIR, or WORKDIR CHAPTERS_DIR')
    parser.add_argument(
        '--wpm', type=float, default=DEFAULT_WPM,
        help=f'TTS speaking rate in words per minute (default: {DEFAULT_WPM})')
    parser.add_argument(
        '--no-duration', action='store_true',
        help='do not add estimated TTS duration to chapter files or index')
    ns = parser.parse_args()

    if len(ns.paths) == 1:
        work, outdir = None, ns.paths[0]
    elif len(ns.paths) == 2:
        work, outdir = ns.paths
    else:
        parser.error('expected CHAPTERS_DIR or WORKDIR CHAPTERS_DIR')
    if ns.wpm <= 0:
        parser.error('--wpm must be greater than zero')

    z, files = read_epub(ns.epub)

    # Prefer meta.json order, but always read the actual title from the EPUB.
    sections = [(name, None) for name in files]
    if work:
        meta_path = os.path.join(work, 'meta.json')
        if os.path.exists(meta_path):
            meta = json.load(open(meta_path, encoding='utf-8'))
            sections = [(s['file'], s['id']) for s in meta.get('sections', [])]

    os.makedirs(outdir, exist_ok=True)
    entries = []
    interlude_no = 0
    used = set()
    wpm_label = f'{ns.wpm:g}'

    for name, sid in sections:
        if name not in z.namelist():
            continue
        if work and sid:
            id_path = os.path.join(work, 'id', f'section-{sid}.txt')
            if not os.path.exists(id_path):
                continue
        title, paras = section_texts(z, name)
        if not paras or AUX_RE.match(title):
            continue
        chapter_match = CHAPTER_RE.match(title)
        if chapter_match:
            fname = f'bab-{int(chapter_match.group(1)):02d}.txt'
        elif INTERLUDE_RE.match(title):
            interlude_no += 1
            fname = f'selingan-{interlude_no:02d}.txt'
        else:
            fname = slug(title) + '.txt'
        base = fname[:-4]
        n = 2
        while fname in used:
            fname = f'{base}-{n}.txt'
            n += 1
        used.add(fname)

        words = len(title.split()) + sum(len(p.split()) for p in paras)
        seconds = words / ns.wpm * 60
        # Keep chapter TXT clean: title + blank line + paragraphs.
        content = title + '\n\n' + '\n\n'.join(paras) + '\n'
        with open(os.path.join(outdir, fname), 'w', encoding='utf-8') as f:
            f.write(content)
        entries.append((fname, words, seconds, title))
        if ns.no_duration:
            print(f'{fname:18s} {words:5d} kata  {title}')
        else:
            print(f'{fname:18s} {words:5d} kata  '
                  f'{format_duration_short(seconds):>10s}  {title}')

    with open(os.path.join(outdir, 'daftar-isi.txt'), 'w', encoding='utf-8') as f:
        f.write('DAFTAR ISI\n\n')
        if ns.no_duration:
            for fname, words, _seconds, title in entries:
                f.write(f'{fname} | {words:5d} kata | {title}\n')
        else:
            f.write(f'Perkiraan durasi TTS: {wpm_label} kata/menit\n\n')
            for fname, words, seconds, title in entries:
                f.write(f'{fname} | {words:5d} kata | '
                        f'{format_duration_short(seconds):>10s} | {title}\n')
            total_words = sum(e[1] for e in entries)
            total_seconds = sum(round(e[2]) for e in entries)
            f.write(f'\nTotal: {len(entries)} chapter | {total_words} kata | '
                    f'{format_duration(total_seconds)}\n')

    if not entries:
        raise SystemExit('No chapters found; check titles or AUX_RE patterns.')
    total_words = sum(e[1] for e in entries)
    if ns.no_duration:
        print(f'{len(entries)} chapter, total {total_words} kata')
    else:
        total_seconds = sum(round(e[2]) for e in entries)
        print(f'{len(entries)} chapter, total {total_words} kata, '
              f'estimasi {format_duration(total_seconds)}')


if __name__ == '__main__':
    main()
