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
<meta name="theme-color" content="#11151b">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
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
pads = ''.join('<button type="button" class="pad" style="--c: %s; %s" aria-label="Hot cue %d" data-pad>%d</button>' % (
    c, ('background: %s; color: #11151b' % c) if i < 3 else 'box-shadow: inset 0 -2px 0 %s' % c, i + 1, i + 1) for i, c in enumerate(colors))
body = re.sub(r'<sc-for list="\{\{pads\}\}".*?</sc-for>', pads, body, flags=re.S)

for key, view, shown in [('isC', 'canvas', False), ('isP', 'perform', True), ('isT', 'timeline', False)]:
    body = re.sub(r'<sc-if value="\{\{%s\}\}" hint-placeholder-val="\{\{ (?:true|false) \}\}">(.*?)</sc-if>' % key,
                  lambda m: '<div class="panel" data-panel="%s"%s>%s</div>' % (view, '' if shown else ' hidden', m.group(1)), body, count=1, flags=re.S)

CAP_P = "Perform: two or four decks around the mixer and library, laid out for playing live."
rep = [
    ('class="win {{goCls}}"', 'class="win js-go"'),
    ('class="band {{bandCls}}"', 'class="band js-go"'),
    ('class="stage {{stageCls}}"', 'class="stage js-go"'),
    ('class="wave {{waveCls}}"', 'class="wave js-go"'),
    ('class="mb play {{playCls}}"', 'class="mb play js-live"'),
    ('class="mb {{syncCls}}" aria-pressed="{{sync}}" onClick="{{toggleSync}}"', 'class="mb sync" aria-pressed="true" data-act="sync"'),
    ('aria-label="{{playLabel}}" aria-pressed="{{playing}}" onClick="{{togglePlay}}"', 'aria-label="Play" aria-pressed="false" data-act="play"'),
    ('aria-pressed="{{playing}}" aria-label="{{playLabel}}" onClick="{{togglePlay}}"', 'aria-pressed="false" aria-label="Play" data-act="play"'),
    ('onClick="{{cue}}"', 'data-act="cue"'),
    ('<span style="color: #97a1b0">{{status}}</span>', '<span style="color: #97a1b0" data-status>Paused</span>'),
    ('<span class="tag" style="font-size: .6875rem">{{hint}}</span>', '<span class="tag" style="font-size: .6875rem" data-hint>Press play</span>'),
    ('class="{{tabC}}" aria-selected="{{selC}}" onClick="{{showC}}"', 'aria-selected="false" data-view="canvas"'),
    ('class="{{tabP}}" aria-selected="{{selP}}" onClick="{{showP}}"', 'class="on" aria-selected="true" data-view="perform"'),
    ('class="{{tabT}}" aria-selected="{{selT}}" onClick="{{showT}}"', 'aria-selected="false" data-view="timeline"'),
    ('aria-label="{{viewName}} view"', 'aria-label="Perform view" data-stage'),
    ('<p class="cap">{{viewCap}}</p>', '<p class="cap" data-cap aria-live="polite">%s</p>' % CAP_P),
]
for a, b in rep:
    n = body.count(a)
    assert n >= 1, a
    body = body.replace(a, b)
assert '{{' not in body and '<sc-' not in body and 'onClick' not in body, re.findall(r'.{40}(?:\{\{|<sc-|onClick).{40}', body)[:5]

script = r'''<script>
(function () {
  var playing = false, sync = true, t;
  var caps = {
    canvas: 'Canvas: lay out every unit, patch keys and MIDI between them, design sounds and build patterns.',
    perform: 'Perform: two or four decks around the mixer and library, laid out for playing live.',
    timeline: 'Timeline: capture what you play, then shape it afterwards with automation.'
  };
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function setPlay(p) {
    playing = p;
    $$('.js-go').forEach(function (e) { e.classList.toggle('go', p); });
    $$('.js-live').forEach(function (e) { e.classList.toggle('lit', p); });
    $$('[data-act="play"]').forEach(function (e) { e.setAttribute('aria-pressed', p ? 'true' : 'false'); e.setAttribute('aria-label', p ? 'Pause' : 'Play'); });
    $$('[data-status]').forEach(function (e) { e.textContent = p ? 'Playing' : 'Paused'; });
    $$('[data-hint]').forEach(function (e) { e.textContent = p ? 'CUE to stop' : 'Press play'; });
  }
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-act],[data-pad],[data-view]');
    if (!b) return;
    if (b.hasAttribute('data-pad')) {
      clearTimeout(t);
      $$('[data-pad]').forEach(function (e) { e.classList.remove('hit'); });
      b.classList.add('hit');
      t = setTimeout(function () { b.classList.remove('hit'); }, 220);
      setPlay(true);
      return;
    }
    if (b.hasAttribute('data-view')) {
      var v = b.getAttribute('data-view');
      $$('[data-view]').forEach(function (e) { var on = e === b; e.classList.toggle('on', on); e.setAttribute('aria-selected', on ? 'true' : 'false'); });
      $$('[data-panel]').forEach(function (e) { e.hidden = e.getAttribute('data-panel') !== v; });
      var st = document.querySelector('[data-stage]');
      if (st) st.setAttribute('aria-label', v.charAt(0).toUpperCase() + v.slice(1) + ' view');
      var c = document.querySelector('[data-cap]');
      if (c) c.textContent = caps[v];
      return;
    }
    var a = b.getAttribute('data-act');
    if (a === 'play') setPlay(!playing);
    else if (a === 'cue') setPlay(false);
    else if (a === 'sync') { sync = !sync; b.classList.toggle('sync', sync); b.setAttribute('aria-pressed', sync ? 'true' : 'false'); }
  });
})();
</script>'''

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
