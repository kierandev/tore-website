"""Build index.html and buy.html from the Design artboards (Main.dc.html, Buy.dc.html).
Usage: python3 tools/build_static.py <folder holding the .dc.html files>
"""
import re, math

import sys, os
SRC = (sys.argv[1] if len(sys.argv) > 1 else 'design') + '/'
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'

def wave(seed, n, lo=10):
    out, s = [], seed
    for i in range(n):
        s = (s * 9301 + 49297) % 233280
        r = s / 233280
        env = 0.45 + 0.55 * abs(math.sin(i / 7))
        out.append('%d%%' % max(lo, math.floor((0.25 + r * 0.75) * env * 100 + 0.5)))
    return out

WAVES = {'wave1': wave(17, 120), 'wave2': wave(53, 120), 'waveBig': wave(91, 200, 14),
         'th1': wave(5, 30), 'th2': wave(29, 30), 'th3': wave(77, 30)}

def split(path):
    h = open(path, encoding='utf-8').read()
    helmet = re.search(r'<helmet>(.*?)</helmet>', h, re.S).group(1).strip()
    body = re.search(r'<x-dc>(.*?)</x-dc>', h, re.S).group(1)
    body = re.sub(r'<helmet>.*?</helmet>', '', body, flags=re.S).strip()
    return helmet, body

def links(body):
    body = body.replace('href="Main.dc.html#', 'href="/#').replace('href="Main.dc.html"', 'href="/"')
    return body.replace('href="Buy.dc.html"', 'href="/buy"')

def head(title, desc, canonical, helmet):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#161616">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{helmet}
<style>html{{scroll-behavior:smooth;scroll-padding-top:72px}}@media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}</style>
</head>
<body>
'''

# ---------- home ----------
helmet, body = split(SRC + 'Main.dc.html')
body = links(body)

def expand(m):
    name, inner = m.group(1), m.group(2)
    return ''.join(inner.replace('{{b.h}}', h) for h in WAVES[name])
body = re.sub(r'<sc-for list="\{\{(\w+)\}\}" as="b" hint-placeholder-count="\d+">(.*?)</sc-for>', expand, body, flags=re.S)

colors = ['#ff4d6d', '#ff8a3d', '#ffd23d', '#59d36b', '#38d6e8', '#3d8bff', '#9b6bff', '#ff5fd2']
pads = ''.join('<button type="button" class="pad%s" style="--c: %s" aria-label="Hot cue %d" data-pad>%d</button>' % (
    ' set' if i < 3 else '', c, i + 1, i + 1) for i, c in enumerate(colors))
body = re.sub(r'<sc-for list="\{\{pads\}\}".*?</sc-for>', pads, body, flags=re.S)

rep = [
    ('class="{{tourCls}}"', 'class="tour s-perform" data-tour'),
    ('aria-selected="{{sel0}}" onClick="{{go0}}"', 'aria-selected="true" data-go="0"'),
    ('aria-selected="{{sel1}}" onClick="{{go1}}"', 'aria-selected="false" data-go="1"'),
    ('aria-selected="{{sel2}}" onClick="{{go2}}"', 'aria-selected="false" data-go="2"'),
    ('aria-label="{{pauseLabel}}" onClick="{{togglePause}}"', 'aria-label="Pause the tour" data-act="pause"'),
]
for a, b in rep:
    assert body.count(a) == 1, a
    body = body.replace(a, b)
assert '{{' not in body and '<sc-' not in body and 'onClick' not in body, re.findall(r'.{40}(?:\{\{|<sc-|onClick).{40}', body)[:5]

script = r"""<script>
(function () {
  var tour = document.querySelector('[data-tour]');
  if (!tour) return;
  var names = ['perform', 'canvas', 'timeline'], MS = 10000;
  var scene = 0, paused = false, timer, start, left = MS, t;
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function show(i) {
    scene = i;
    names.forEach(function (n) { tour.classList.remove('s-' + n); });
    void tour.offsetWidth; // restart the scene's animations even when re-selecting the same view
    tour.classList.add('s-' + names[i]);
    $$('[data-go]').forEach(function (b) { b.setAttribute('aria-selected', +b.getAttribute('data-go') === i ? 'true' : 'false'); });
  }
  function arm(ms) {
    clearTimeout(timer); left = ms; start = Date.now();
    timer = setTimeout(function () { show((scene + 1) % 3); arm(MS); }, ms);
  }
  function setPaused(p) {
    paused = p;
    tour.classList.toggle('paused', p);
    var b = document.querySelector('[data-act="pause"]');
    if (b) b.setAttribute('aria-label', p ? 'Play the tour' : 'Pause the tour');
  }
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-go],[data-act="pause"],[data-pad]');
    if (!b) return;
    if (b.hasAttribute('data-pad')) {
      clearTimeout(t);
      $$('[data-pad]').forEach(function (e) { e.classList.remove('hit'); });
      b.classList.add('hit');
      t = setTimeout(function () { b.classList.remove('hit'); }, 220);
    } else if (b.hasAttribute('data-go')) {
      show(+b.getAttribute('data-go'));
      if (paused) left = MS; else arm(MS);
    } else if (paused) {
      setPaused(false); arm(left || MS);
    } else {
      clearTimeout(timer);
      left = Math.max(500, left - (Date.now() - start));
      setPaused(true);
    }
  });
  // don't run the tour in a background tab
  document.addEventListener('visibilitychange', function () {
    if (paused) return;
    if (document.hidden) { clearTimeout(timer); left = Math.max(500, left - (Date.now() - start)); tour.classList.add('paused'); }
    else { tour.classList.remove('paused'); arm(left); }
  });
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) setPaused(true); else arm(MS);
})();
</script>"""

home = head('TORE – DJ, produce and perform in one Mac app',
            'TORE brings decks, a mixer, a drum machine, a sampler, an FM synth, a sequencer and a recorder together on one canvas. In pre-alpha – not yet available.',
            'https://toreaudio.com/', helmet) + body + '\n' + script + '\n</body>\n</html>\n'
# the static page has no Design-canvas root sizing: panels hidden by attribute must stay hidden
home = home.replace('</style>\n</head>', '[hidden]{display:none !important}</style>\n</head>', 1)
open(OUT + 'index.html', 'w', encoding='utf-8').write(home)

# ---------- availability (/buy) ----------
helmet, body = split(SRC + 'Buy.dc.html')
body = links(body)
assert '{{' not in body and '<sc-' not in body
buy = head('TORE – Availability', 'TORE is in pre-alpha and not yet available to buy. Get notified when it is.',
           'https://toreaudio.com/buy', helmet) + body + '\n</body>\n</html>\n'
open(OUT + 'buy.html', 'w', encoding='utf-8').write(buy)
print('built', len(home), len(buy))
