#!/usr/bin/env python3
"""
Filsrafat static site generator.

Membaca _posts/YYYY-MM-DD-slug.md (front matter: title, date),
menulis HTML statis + .nojekyll sehingga GitHub Pages menyajikan
langsung tanpa build Jekyll.

Cara pakai harian:
    1. Tulis _posts/YYYY-MM-DD-<slug>.md
    2. python3 build.py
    3. git add -A && git commit -m "..." && git push origin main

Subset Markdown yang didukung: heading (#, ##, ###), paragraf,
**bold**, *italic*, `code`, [teks](url), list (- / 1.), blockquote (>).
"""

import os
import re
import html as htmlmod
from datetime import datetime, date

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "_posts")
BASE = "/filsrafat-blog"  # baseurl situs saat live

BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
         "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
BULAN_S = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
           "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def tgl_id(d, pendek=False):
    b = BULAN_S if pendek else BULAN
    return f"{d.day} {b[d.month]} {d.year}"


def inline_md(t):
    t = htmlmod.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', t)
    return t


def md_to_html(md):
    blocks = re.split(r"\n\s*\n", md.strip())
    out = []
    for b in blocks:
        b = b.rstrip()
        if not b:
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", b, re.S)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline_md(m.group(2).strip())}</h{lvl}>")
            continue
        if all(re.match(r"^\s*>\s?", l) for l in b.split("\n")):
            inner = "\n".join(re.sub(r"^\s*>\s?", "", l) for l in b.split("\n"))
            out.append(f"<blockquote><p>{inline_md(inner.strip())}</p></blockquote>")
            continue
        lines = b.split("\n")
        if all(re.match(r"^\s*[-*]\s+", l) for l in lines):
            items = "".join(f"<li>{inline_md(re.sub(r'^\\s*[-*]\\s+', '', l).strip())}</li>"
                            for l in lines)
            out.append(f"<ul>{items}</ul>")
            continue
        if all(re.match(r"^\s*\d+\.\s+", l) for l in lines):
            items = "".join(f"<li>{inline_md(re.sub(r'^\\s*\\d+\\.\\s+', '', l).strip())}</li>"
                            for l in lines)
            out.append(f"<ol>{items}</ol>")
            continue
        out.append(f"<p>{inline_md(' '.join(l.strip() for l in lines))}</p>")
    return "\n".join(out)


BASE_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title_tag}</title>
  <meta name="description" content="{desc}">
  <link rel="stylesheet" href="{base}/assets/css/style.css">
</head>
<body>
  <header class="site-header">
    <div class="wrap">
      <a class="site-title" href="{base}/">Filsrafat</a>
      <nav class="site-nav">
        <a href="{base}/">Beranda</a>
        <a href="{base}/tentang/">Tentang</a>
      </nav>
    </div>
    <p class="tagline">Bukan motivator. Cuma orang yang kebanyakan mikir.</p>
  </header>
  <main class="wrap content">
{content}
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <p>Filsrafat &mdash; mikirin hidup lewat kata-kata para filsuf.</p>
    </div>
  </footer>
</body>
</html>
"""

ABOUT_BODY = """<h2>Tentang Filsrafat</h2>
<p>Filsrafat itu gabungan kata filsafat dan Usra. Tempat buat mikirin hidup lewat quote dan pemikiran para filsuf, dibawain pake bahasa santai yang gampang dicerna.</p>
<p>Bukan motivator. Cuma orang yang kebanyakan mikir.</p>
<p>Di sini lu bakal nemu quote para filsuf, bedah konsep filsafat dengan bahasa sehari-hari, dan opini jujur tentang hidup. Semua ditulis buat anak muda yang penasaran, bukan buat yang udah punya gelar filsafat.</p>"""


def parse_post(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        raise ValueError(f"Front matter tidak valid: {path}")
    meta = yaml.safe_load(m.group(1))
    body = m.group(2)
    title = str(meta.get("title", "Tanpa judul"))
    d = meta.get("date")
    if isinstance(d, datetime):
        d = d.date()
    elif isinstance(d, str):
        d = datetime.strptime(d.strip(), "%Y-%m-%d").date()
    if not isinstance(d, date):
        raise ValueError(f"Tanggal tidak valid di {path}")
    slug = os.path.basename(path)[11:-3]  # potong YYYY-MM-DD- dan .md
    url = f"{BASE}/{d.year}/{d.month:02d}/{d.day:02d}/{slug}/"
    return {"title": title, "date": d, "slug": slug, "url": url,
            "html": md_to_html(body)}


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    posts = []
    for fn in sorted(os.listdir(POSTS_DIR)):
        if fn.endswith(".md"):
            posts.append(parse_post(os.path.join(POSTS_DIR, fn)))
    posts.sort(key=lambda p: p["date"], reverse=True)

    # index
    items = "\n".join(
        f'  <li>\n    <span class="post-date">{tgl_id(p["date"], pendek=True)}</span>\n'
        f'    <a class="post-link" href="{p["url"]}">{htmlmod.escape(p["title"])}</a>\n  </li>'
        for p in posts
    )
    index_body = ('<h2 class="section-title">Tulisan terbaru</h2>\n<ul class="post-list">\n'
                  + items + '\n</ul>') if posts else \
        '<h2 class="section-title">Tulisan terbaru</h2>\n<p>Belum ada tulisan. Sabar, lagi mikir.</p>'
    write(os.path.join(ROOT, "index.html"),
          BASE_HTML.format(title_tag="Filsrafat", desc="Bukan motivator. Cuma orang yang kebanyakan mikir.",
                           base=BASE, content=index_body))

    # tentang
    write(os.path.join(ROOT, "tentang", "index.html"),
          BASE_HTML.format(title_tag="Tentang Filsrafat | Filsrafat",
                           desc="Filsrafat itu gabungan kata filsafat dan Usra.",
                           base=BASE, content=ABOUT_BODY))

    # posts
    for p in posts:
        body = (f'<article class="post">\n<header class="post-header">\n'
                f'<h1 class="post-title">{htmlmod.escape(p["title"])}</h1>\n'
                f'<p class="post-meta">{tgl_id(p["date"])}</p>\n</header>\n'
                f'<div class="post-body">\n{p["html"]}\n</div>\n'
                f'<p class="back"><a href="{BASE}/">&larr; Kembali ke beranda</a></p>\n</article>')
        dest = os.path.join(ROOT, str(p["date"].year), f"{p['date'].month:02d}",
                            f"{p['date'].day:02d}", p["slug"], "index.html")
        write(dest, BASE_HTML.format(title_tag=f"{p['title']} | Filsrafat",
                                     desc=p["title"][:150], base=BASE, content=body))

    # .nojekyll supaya GitHub Pages menyajikan file apa adanya
    write(os.path.join(ROOT, ".nojekyll"), "")

    print(f"OK: {len(posts)} artikel -> index, tentang, halaman artikel, .nojekyll")


if __name__ == "__main__":
    main()
