#!/usr/bin/env python3
"""Build an Indonesian EPUB from a source EPUB and paragraph-aligned translations.

Usage:
    python3 build_epub.py SOURCE.epub WORKDIR OUTPUT.epub

WORKDIR must contain:
    meta.json              (from extract_sections.py)
    id/section-XXXX.txt    (translated title + one paragraph per line)

Optional:
    auxiliary.json         {"English phrase": "Frasa Indonesia", ...}
    metadata.json          {"title": "...", "creator": "...", "identifier": "..."}

The builder preserves the original XHTML head/body attributes, re-inserts
inline images using meta.json, keeps every original image file, translates
TOC/NCX labels, normalises images for e-readers, and provides an <img>
fallback for an SVG cover.
"""
import sys, os, re, json, html, shutil, zipfile


def esc(s):
    return html.escape(s, quote=False)


def markup(text):
    text = (text.replace('{i}', '\x01').replace('{/i}', '\x02')
            .replace('{b}', '\x03').replace('{/b}', '\x04'))
    text = re.sub(r'\*([^*\n]+)\*', '\x01\\1\x02', text)
    text = esc(text)
    return (text.replace('\x01', '<em>').replace('\x02', '</em>')
            .replace('\x03', '<strong>').replace('\x04', '</strong>'))


def paragraph(text, cls='P_Prose_Formatting'):
    return f'<p class="{cls}"><span style=" font-size: 1.00em;">{markup(text)}</span></p>'


def normalise_img(m):
    tag = m.group(0)
    src = re.search(r'src="([^"]+)"', tag)
    if not src:
        return tag
    ident = re.search(r'id="([^"]+)"', tag)
    alt = re.search(r'alt="([^"]*)"', tag)
    attrs = f' alt="{alt.group(1) if alt else ""}"'
    if ident:
        attrs += f' id="{ident.group(1)}"'
    logo = 'sevenseaslogo' in (ident.group(1) if ident else '')
    style = ('max-width: 100%; height: auto; display: block; margin: 0 auto;'
             if logo else
             'width: 100%; max-width: 100%; height: auto; display: block; margin: 0 auto;')
    width = '' if logo else ' width="100%"'
    return f'<img{attrs} src="{src.group(1)}"{width} style="{style}"/>'


def replace_text(text, old, new):
    """Replace only in text nodes, never in tag attributes or file paths."""
    parts = re.split(r'(<[^>]*>)', text)
    return ''.join(
        part if part.startswith('<') else part.replace(old, new)
        for part in parts
    )


def set_html_lang(doc):
    m = re.search(r'<html\b[^>]*>', doc, re.I)
    if not m:
        return doc
    tag = m.group(0)
    if re.search(r'xml:lang\s*=', tag, re.I):
        tag = re.sub(r'xml:lang\s*=\s*"[^"]*"', 'xml:lang="id"', tag, flags=re.I)
    else:
        tag = tag[:-1] + ' xml:lang="id">'
    tag = re.sub(r'\slang\s*=\s*"[^"]*"', ' lang="id"', tag, flags=re.I)
    return doc[:m.start()] + tag + doc[m.end():]


def body_wrapper(inner):
    """Return a single top-level <div> wrapper from the original body, if any."""
    s = inner.strip()
    m = re.match(r'(<div\b[^>]*>)(.*)(</div>)\s*$', s, re.S | re.I)
    if m and s.lower().count('<div') == 1:
        return m.group(1), m.group(3)
    return '', ''


def build_section(section, id_path, build_dir):
    lines = [l.rstrip('\n') for l in open(id_path, encoding='utf-8') if l.strip()]
    if not lines:
        return None
    title, body = lines[0].strip(), lines[1:]
    title_html = esc(title)
    if ':' in title:
        a, b = title.split(':', 1)
        title_html = esc(a.strip()) + ':<br/>' + esc(b.strip())

    images = {}
    for im in section.get('images', []):
        images.setdefault(int(im['index']), []).append(im['tag'])
    parts = []
    # An image at index 0 came before the first text paragraph in the source,
    # so keep it before the generated title heading as well.
    if 0 in images:
        parts.extend(images[0])
    parts += [
        '<p class="P__STAR__STAR__STAR__page_break" id="auto_bookmark_toc_top">'
        '<span><span style=" font-weight: bold; font-size: 1.17em;">'
        + title_html + '</span></span></p>',
        '<p class="P_Prose_Formatting">&#160;</p>',
    ]
    all_lines = [title] + body
    for i, line in enumerate(all_lines):
        if i in images and i != 0:
            parts.extend(images[i])
        if i == 0:
            continue
        line = line.strip()
        if line == '***':
            parts.append('<p class="P__STAR__STAR__STAR__page_break"><span><span style=" font-size: 1.00em;">***</span></span></p>')
            parts.append('<p class="P_Prose_Formatting">&#160;</p>')
        else:
            parts.append(paragraph(line))
    if len(all_lines) in images:
        parts.extend(images[len(all_lines)])
    body_html = os.linesep.join(parts)

    original = os.path.join(build_dir, section['file'])
    if os.path.exists(original):
        doc = open(original, encoding='utf-8').read()
        bm = re.search(r'<body\b[^>]*>', doc, re.I)
        be = re.search(r'</body\s*>', doc[bm.end():], re.I) if bm else None
        if bm and be:
            old_inner = doc[bm.end():bm.end() + be.start()]
            wrap_open, wrap_close = body_wrapper(old_inner)
            new_inner = (wrap_open + os.linesep + body_html + os.linesep
                         + wrap_close)
            doc = (doc[:bm.end()] + new_inner
                   + doc[bm.end() + be.start():])
        else:
            doc = None
    else:
        doc = None

    if doc is None:
        doc = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="id">
<head>
<meta content="application/xhtml+xml; charset=UTF-8" http-equiv="Content-Type"/>
<title>{esc(title)}</title>
</head>
<body>
{body_html}
</body>
</html>
'''
    else:
        if re.search(r'<title\b', doc, re.I):
            doc = re.sub(r'<title[^>]*>.*?</title>',
                         f'<title>{esc(title)}</title>', doc, count=1,
                         flags=re.S | re.I)
        else:
            doc = re.sub(r'</head\s*>',
                         f'<title>{esc(title)}</title></head>', doc,
                         count=1, flags=re.I)
        doc = set_html_lang(doc)

    out = os.path.join(build_dir, section['file'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(doc)
    return title


def all_files(build, suffixes):
    for root, dirs, files in os.walk(build):
        dirs.sort()
        for f in sorted(files):
            if f.lower().endswith(suffixes):
                yield os.path.join(root, f)


def set_metadata(doc, tag, value):
    value = esc(str(value))
    pattern = rf'<{re.escape(tag)}(\s[^>]*)?>.*?</{re.escape(tag)}\s*>'
    if re.search(pattern, doc, re.S | re.I):
        return re.sub(
            pattern,
            lambda m: f'<{tag}{m.group(1) or ""}>{value}</{tag}>',
            doc, count=1, flags=re.S | re.I)
    return doc.replace('</metadata>', f'<{tag}>{value}</{tag}>\n</metadata>', 1)


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    source, work, out_epub = sys.argv[1], sys.argv[2], sys.argv[3]
    meta = json.load(open(os.path.join(work, 'meta.json'), encoding='utf-8'))
    build = os.path.join(work, 'build')
    if os.path.isdir(build):
        shutil.rmtree(build)
    os.makedirs(build)
    with zipfile.ZipFile(source) as z:
        z.extractall(build)

    translated = {}
    for section in meta['sections']:
        id_path = os.path.join(work, 'id', f"section-{section['id']}.txt")
        if not os.path.exists(id_path):
            continue
        lines = [l for l in open(id_path, encoding='utf-8') if l.strip()]
        if len(lines) != section['paragraphs']:
            print(f"WARNING: section {section['id']}: {len(lines)} lines, "
                  f"expected {section['paragraphs']}")
        title = build_section(section, id_path, build)
        if title:
            translated[section['title']] = title

    # Labels used on auxiliary pages and in the TOC/NCX. Extend this map for
    # books with different front/back matter.
    common_labels = {
        'Color Inserts': 'Sisipan Berwarna',
        'Title Page': 'Halaman Judul',
        'Copyrights and Credits': 'Hak Cipta dan Kredit',
        'Table of Contents Page': 'Halaman Daftar Isi',
        'Table of Contents': 'Daftar Isi',
        'Character Design Concepts': 'Konsep Desain Karakter',
        'About the Author:': 'Tentang Penulis:',
        'About the Author': 'Tentang Penulis',
        'Newsletter': 'Buletin',
    }
    # Applied only to an exact <title>, so generic words cannot corrupt prose.
    title_labels = {
        'Cover': 'Sampul',
        'Copyright': 'Hak Cipta',
        'jln': 'Iklan',
    }

    # Promotional lines that are not part of a translatable section file.
    aux_replacements = {
        'Download all your Fav Light Novels from': 'Unduh semua novel ringan favoritmu dari',
        'Download all your favorite Light Novels from': 'Unduh semua novel ringan favoritmu dari',
    }
    aux_path = os.path.join(work, 'auxiliary.json')
    if os.path.exists(aux_path):
        aux_replacements.update(json.load(open(aux_path, encoding='utf-8')))

    replacements = {}
    replacements.update(translated)
    replacements.update(common_labels)
    replacements.update(aux_replacements)
    # Longest source string first so a short label cannot eat a longer title.
    ordered = sorted(replacements.items(), key=lambda kv: len(kv[0]), reverse=True)

    # Update all HTML/NCX labels and auxiliary text. This works regardless of
    # the EPUB's TOC filename and never touches href/src attributes.
    for p in all_files(build, ('.html', '.xhtml', '.ncx')):
        t = open(p, encoding='utf-8').read()
        for old, new in ordered:
            t = replace_text(t, esc(old), esc(new))
            t = replace_text(t, old, new)
        for old, new in title_labels.items():
            t = re.sub(
                rf'<title[^>]*>\s*{re.escape(old)}\s*</title>',
                f'<title>{esc(new)}</title>', t, flags=re.I)
        t = t.replace('xml:lang="en"', 'xml:lang="id"')
        open(p, 'w', encoding='utf-8').write(t)

    # Metadata language, plus optional title/creator/identifier overrides.
    opf_path = next(all_files(build, ('.opf',)), None)
    if opf_path:
        t = open(opf_path, encoding='utf-8').read()
        t = re.sub(r'<dc:language[^>]*>[^<]*</dc:language>',
                   '<dc:language>id</dc:language>', t)
        meta_path = os.path.join(work, 'metadata.json')
        if os.path.exists(meta_path):
            data = json.load(open(meta_path, encoding='utf-8'))
            for key, tag in [('title', 'dc:title'), ('creator', 'dc:creator'),
                             ('identifier', 'dc:identifier')]:
                if data.get(key):
                    t = set_metadata(t, tag, data[key])
        open(opf_path, 'w', encoding='utf-8').write(t)

    # Normalise images and add page breaks around chapter illustrations.
    for p in all_files(build, ('.html', '.xhtml')):
        t = open(p, encoding='utf-8').read()
        t = re.sub(r'<img\b[^>]*>', normalise_img, t)
        t = re.sub(
            r'<p class="([^"]*PAGEBREAK[^"]*)"([^>]*)>(\s*<span[^>]*>\s*<img)',
            lambda m: f'<p class="{m.group(1)}" style="page-break-before: always; page-break-after: always;"{m.group(2)}>{m.group(3)}',
            t)
        open(p, 'w', encoding='utf-8').write(t)

    # Cover fallback: replace an SVG wrapper containing an image with a plain
    # responsive <img>, because EPUB2 readers often cannot render SVG covers.
    # Only touch pages that look like a cover, not inline SVG illustrations.
    for p in all_files(build, ('.html', '.xhtml')):
        t = open(p, encoding='utf-8').read()
        base = os.path.basename(p).lower()
        if 'cover' not in base and not re.search(
                r'<title[^>]*>\s*(cover|sampul)\s*</title>', t, re.I):
            continue
        m = re.search(r'<svg\b.*?</svg>', t, re.S | re.I)
        if not m or '<image' not in m.group(0).lower():
            continue
        src = re.search(r'(?:xlink:)?href="([^"]+)"', m.group(0), re.I)
        if not src:
            continue
        fallback = (
            '<div style="text-align:center;padding:0;margin:0;">'
            f'<img alt="Sampul" src="{src.group(1)}" '
            'style="width:100%;max-width:100%;height:auto;display:block;margin:0 auto;"/>'
            '</div>')
        t = t[:m.start()] + fallback + t[m.end():]
        t = re.sub(r'<title[^>]*>.*?</title>', '<title>Sampul</title>',
                   t, count=1, flags=re.S | re.I)
        open(p, 'w', encoding='utf-8').write(t)

    # Package EPUB: mimetype first, uncompressed, with the exact required bytes.
    out_dir = os.path.dirname(os.path.abspath(out_epub))
    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(out_epub):
        os.remove(out_epub)
    with zipfile.ZipFile(out_epub, 'w') as z:
        z.writestr('mimetype', b'application/epub+zip',
                   compress_type=zipfile.ZIP_STORED)
        for root, dirs, files in os.walk(build):
            dirs.sort()
            files.sort()
            for f in files:
                p = os.path.join(root, f)
                arc = os.path.relpath(p, build).replace('\\', '/')
                if arc == 'mimetype':
                    continue
                z.write(p, arc, compress_type=zipfile.ZIP_DEFLATED)
    print(f'written {out_epub} ({os.path.getsize(out_epub)} bytes)')
    print(f'sections translated: {len(translated)}')


if __name__ == '__main__':
    main()
