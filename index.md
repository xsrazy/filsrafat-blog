---
layout: default
title: Beranda
---
<h2 class="section-title">Tulisan terbaru</h2>
<ul class="post-list">
{% for post in site.posts %}
  <li>
    <span class="post-date">{{ post.date | date: "%-d %b %Y" }}</span>
    <a class="post-link" href="{{ post.url | relative_url }}">{{ post.title }}</a>
  </li>
{% endfor %}
</ul>
{% if site.posts.size == 0 %}
<p>Belum ada tulisan. Sabar, lagi mikir.</p>
{% endif %}
