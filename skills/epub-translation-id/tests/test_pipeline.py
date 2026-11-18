#!/usr/bin/env python3
"""End-to-end smoke test for the epub-translation-id scripts.

Creates a tiny synthetic EPUB (no copyrighted content), runs the full pipeline,
and asserts image preservation, TOC translation, cover fallback, validation,
and chapter extraction.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PY = sys.executable


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_fixture(base):
    src = base / "fixture-src"
    write(src / "mimetype", "application/epub+zip")
    write(src / "META-INF/container.xml", """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""")
    write(src / "OEBPS/content.opf", """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Mini Book</dc:title>
    <dc:language>en</dc:language>
    <dc:identifier id="BookId">urn:uuid:mini</dc:identifier>
  </metadata>
  <manifest>
    <item id="cover" href="Text/CoverPage.html" media-type="application/xhtml+xml"/>
    <item id="toc" href="Text/TableOfContents.html" media-type="application/xhtml+xml"/>
    <item id="ch1" href="Text/chapter1.html" media-type="application/xhtml+xml"/>
    <item id="ch2" href="Text/chapter2.html" media-type="application/xhtml+xml"/>
    <item id="ch3" href="Text/chapter3.html" media-type="application/xhtml+xml"/>
    <item id="about" href="Text/about.html" media-type="application/xhtml+xml"/>
    <item id="jln" href="Text/jln.html" media-type="application/xhtml+xml"/>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="Styles/styles.css" media-type="text/css"/>
    <item id="coverimg" href="Images/cover.jpg" media-type="image/jpeg"/>
    <item id="pic" href="Images/pic.png" media-type="image/png"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="cover"/>
    <itemref idref="toc"/>
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
    <itemref idref="ch3"/>
    <itemref idref="about"/>
    <itemref idref="jln"/>
  </spine>
</package>
""")
    write(src / "OEBPS/toc.ncx", """<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head/><docTitle><text>Mini Book</text></docTitle>
  <navMap>
    <navPoint id="n1" playOrder="1"><navLabel><text>Chapter 1: Start</text></navLabel><content src="Text/chapter1.html"/></navPoint>
    <navPoint id="n2" playOrder="2"><navLabel><text>Chapter 2: End</text></navLabel><content src="Text/chapter2.html"/></navPoint>
  </navMap>
</ncx>
""")
    write(src / "OEBPS/Text/CoverPage.html", """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:xlink="http://www.w3.org/1999/xlink">
<head><title>Cover</title></head>
<body><svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="100%" height="100%">
<image xlink:href="../Images/cover.jpg" width="100%" height="100%"/>
</svg></body></html>
""")
    write(src / "OEBPS/Text/TableOfContents.html", """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Table of Contents</title></head>
<body><h1>Table of Contents</h1>
<p><a href="chapter1.html">Chapter 1: Start</a></p>
<p><a href="chapter2.html">Chapter 2: End</a></p>
</body></html>
""")
    write(src / "OEBPS/Text/chapter1.html", """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 1: Start</title></head>
<body>
<h1>Chapter 1: Start</h1>
<p>The morning was cold.</p>
<p><img src="../Images/pic.png" alt=""/></p>
<p>She opened the door.</p>
<p>She was <i>very</i> <b>sure</b>.</p>
<p>***</p>
<p>Then she left.</p>
</body></html>
""")
    write(src / "OEBPS/Text/chapter2.html", """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 2: End</title></head>
<body><h1>Chapter 2: End</h1><p>That was the end.</p></body></html>
""")
    # No visible title heading in the body: image index must still line up
    # after the generated title heading.
    write(src / "OEBPS/Text/chapter3.html", """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 3: Extra</title></head>
<body>
<p>First part.</p>
<p><img src="../Images/pic.png" alt=""/></p>
<p>Second part.</p>
</body></html>
""")
    write(src / "OEBPS/Text/about.html", """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>About the Author</title></head>
<body><h1>About the Author</h1><p>The author lives in a small town.</p></body></html>
""")
    write(src / "OEBPS/Text/jln.html", """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>jln</title></head>
<body><p>Download all your Fav Light Novels from <a href="https://www.justlightnovels.com/">Just Light Novels</a></p></body></html>
""")
    write(src / "OEBPS/Styles/styles.css", "body { font-family: serif; }\n")
    (src / "OEBPS/Images").mkdir(parents=True, exist_ok=True)
    (src / "OEBPS/Images/cover.jpg").write_bytes(b"fake-jpeg-bytes")
    (src / "OEBPS/Images/pic.png").write_bytes(b"fake-png-bytes")

    epub = base / "mini.epub"
    with zipfile.ZipFile(epub, "w") as z:
        z.write(src / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for p in sorted(src.rglob("*")):
            if p.is_file() and p.name != "mimetype":
                z.write(p, p.relative_to(src).as_posix(),
                        compress_type=zipfile.ZIP_DEFLATED)
    return epub


def run(*args):
    cmd = [PY, *map(str, args)]
    print("+", " ".join(map(str, args)))
    subprocess.run(cmd, check=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with tempfile.TemporaryDirectory(prefix="epub-skill-test-") as td:
        base = Path(td)
        epub = make_fixture(base)
        work = base / "work"

        run(SCRIPTS / "extract_sections.py", epub, work)
        meta = json.loads((work / "meta.json").read_text(encoding="utf-8"))
        by_title = {s["title"]: s for s in meta["sections"]}
        assert set(by_title) == {
            "Chapter 1: Start", "Chapter 2: End", "Chapter 3: Extra",
            "About the Author"
        }, by_title.keys()
        ch1 = by_title["Chapter 1: Start"]
        assert len(ch1["images"]) == 1
        assert ch1["images"][0]["index"] == 2, ch1["images"]
        ch3 = by_title["Chapter 3: Extra"]
        assert len(ch3["images"]) == 1
        assert ch3["images"][0]["index"] == 2, ch3["images"]

        ids = {
            ch1["id"]: """Bab 1: Awal
Pagi itu dingin.
Dia membuka pintu.
Dia {i}sangat{/i} {b}yakin{/b}.
***
Lalu dia pergi.
""",
            by_title["Chapter 2: End"]["id"]: """Bab 2: Akhir
Itulah akhirnya.
""",
            by_title["Chapter 3: Extra"]["id"]: """Bab 3: Tambahan
Bagian pertama.
Bagian kedua.
""",
            by_title["About the Author"]["id"]: """Tentang Penulis
Penulis tinggal di kota kecil.
""",
        }
        for sid, text in ids.items():
            write(work / "id" / f"section-{sid}.txt", text)

        out = base / "out.epub"
        run(SCRIPTS / "build_epub.py", epub, work, out)
        run(SCRIPTS / "validate_epub.py", epub, out, work)
        report = (work / "validation.txt").read_text(encoding="utf-8")
        assert "issues: 0" in report, report
        assert "image positions checked: 2" in report, report

        # Images must be byte-identical.
        with zipfile.ZipFile(epub) as src, zipfile.ZipFile(out) as dst:
            for name in ("OEBPS/Images/cover.jpg", "OEBPS/Images/pic.png"):
                assert src.read(name) == dst.read(name), name
            cover = dst.read("OEBPS/Text/CoverPage.html").decode()
            assert "<img" in cover
            assert "Sampul" in cover
            toc = dst.read("OEBPS/Text/TableOfContents.html").decode()
            assert "Bab 1: Awal" in toc and "Bab 2: Akhir" in toc
            jln = dst.read("OEBPS/Text/jln.html").decode()
            assert "Unduh semua novel ringan favoritmu dari" in jln
            ch1_html = dst.read("OEBPS/Text/chapter1.html").decode()
            assert "<em>sangat</em>" in ch1_html
            assert "<strong>yakin</strong>" in ch1_html
            opf = dst.read("OEBPS/content.opf").decode()
            assert "<dc:language>id</dc:language>" in opf

        chapters = base / "chapters"
        run(SCRIPTS / "extract_chapters.py", out, work, chapters)
        bab1 = (chapters / "bab-01.txt").read_text(encoding="utf-8")
        assert bab1.startswith("Bab 1: Awal\n\nPagi itu dingin.")
        assert "Perkiraan durasi TTS" not in bab1
        assert "\n\n***\n\n" in bab1
        assert "Dia sangat yakin." in bab1
        assert (chapters / "bab-02.txt").exists()
        bab3 = (chapters / "bab-03.txt").read_text(encoding="utf-8")
        assert bab3.startswith("Bab 3: Tambahan\n\nBagian pertama.")
        assert "Perkiraan durasi TTS" not in bab3
        assert not (chapters / "tentang-penulis.txt").exists()
        index = (chapters / "daftar-isi.txt").read_text(encoding="utf-8")
        assert "Perkiraan durasi TTS: 140 kata/menit" in index
        assert "bab-01.txt" in index
        assert "Total: 3 chapter" in index

        # Custom WPM affects the index, not the chapter TXT.
        chapters_wpm = base / "chapters-wpm"
        run(SCRIPTS / "extract_chapters.py", out, work, chapters_wpm, "--wpm", "120")
        assert "Perkiraan durasi TTS: 120 kata/menit" in (
            chapters_wpm / "daftar-isi.txt").read_text(encoding="utf-8")
        assert "Perkiraan durasi TTS" not in (
            chapters_wpm / "bab-01.txt").read_text(encoding="utf-8")

        chapters_plain = base / "chapters-plain"
        run(SCRIPTS / "extract_chapters.py", out, work, chapters_plain,
            "--no-duration")
        plain = (chapters_plain / "bab-01.txt").read_text(encoding="utf-8")
        assert plain.startswith("Bab 1: Awal\n\nPagi itu dingin.")
        assert "Perkiraan durasi TTS" not in (
            chapters_plain / "daftar-isi.txt").read_text(encoding="utf-8")

        # Without meta.json, the same story chapters must be found.
        chapters2 = base / "chapters2"
        run(SCRIPTS / "extract_chapters.py", out, chapters2)
        assert (chapters2 / "bab-01.txt").exists()
        assert (chapters2 / "bab-02.txt").exists()
        assert (chapters2 / "bab-03.txt").exists()

        print("OK: synthetic EPUB pipeline passed")


if __name__ == "__main__":
    main()
