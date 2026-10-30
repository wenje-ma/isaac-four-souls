// v5: keeps the markup, not just the text.
//
// v4 read textContent, which throws away every <img> inside the effect line.
// Those images are the icons the printed card shows in the middle of a sentence
// (coin, heart, D6, sword, soul), so cards came out as "they gain 1$" or
// "equal to its ." with a hole where the icon was. This version stores the
// innerHTML of each effect block and the src basename of every icon, so the
// cleaned text can put a readable token back in the right place.
//
// Paste into the DevTools console of a foursouls.com tab that already passed
// Cloudflare. It writes one JSON file at the end. START exists only to resume a
// run that died; leave it at 0 for a full pass.

const START = 0;
const LIMIT = 0;

(async () => {
  const CONC = 3;
  const RETRY = 3;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const dom = (html) => new DOMParser().parseFromString(html, 'text/html');

  const once = async (u) => {
    const r = await fetch(u, { credentials: 'include' });
    if (!r.ok) throw new Error(r.status + ' ' + u);
    const t = await r.text();
    if (t.indexOf('Just a moment') > -1) throw new Error('challenge ' + u);
    return t;
  };

  const grab = async (u) => {
    let last;
    for (let i = 0; i <= RETRY; i++) {
      try {
        return await once(u);
      } catch (e) {
        last = e;
        if (e.message.indexOf('challenge') === 0) throw e;
        await sleep(500 * (i + 1));
      }
    }
    throw last;
  };

  const slugOf = (href) => {
    if (!href) return null;
    try {
      const u = new URL(href, location.href);
      const p = u.pathname;
      if (p.indexOf('/cards/') === 0 && p !== '/cards/') return p;
    } catch (e) {}
    return null;
  };

  // ---- enumerate every card page, the same way v4 did
  const idx = dom(await grab('/cards/'));
  const filters = [...new Set([...idx.querySelectorAll('a')]
    .map((a) => a.getAttribute('href') || '')
    .filter((h) => h.indexOf('card-search') > -1))]
    .map((h) => new URL(h, location.href));
  const origins = [...new Set(filters.map((u) => u.searchParams.get('origin')).filter(Boolean))];
  const types = [...new Set(filters.map((u) => u.searchParams.get('card_type')).filter(Boolean))];

  const urls = filters.map((u) => u.href);
  for (const o of origins) for (const t of types) {
    const u = new URL('/card-search/', location.origin);
    u.searchParams.set('origin', o);
    u.searchParams.set('card_type', t);
    urls.push(u.href);
  }
  console.log('origins', origins.length, '| types', types.length, '| enum urls', urls.length);

  const slugs = new Set();
  let done = 0;
  const worker = async (start) => {
    for (let i = start; i < urls.length; i += CONC) {
      try {
        const d = dom(await grab(urls[i]));
        d.querySelectorAll('a').forEach((a) => {
          const s = slugOf(a.getAttribute('href'));
          if (s) slugs.add(s);
        });
      } catch (e) {
        console.warn('enum fail', urls[i], e.message);
      }
      done++;
      if (done % 60 === 0) console.log('enum', done, '/', urls.length, 'unique', slugs.size);
      await sleep(60);
    }
  };
  await Promise.all(Array.from({ length: CONC }, (_, k) => worker(k)));

  const all = [...slugs].sort();
  const list = all.slice(START, LIMIT > 0 ? START + LIMIT : undefined);
  console.log('enumerated', all.length, '| this run', list.length);

  // ---- one card, markup kept
  const iconName = (src) => {
    if (!src) return 'unknown';
    const file = src.split('/').pop().split('?')[0];
    return file.replace(/\.(png|jpe?g|svg|gif|webp)$/i, '').replace(/-\d+x\d+$/, '');
  };
  const inventory = {};

  const extract = (slug, d) => {
    const info = d.querySelector('#CardInfo');
    const display = d.querySelector('#CardDisplay');
    const ps = info && info.querySelector('#OriginSet')
      ? [...info.querySelectorAll('#OriginSet p')].map((p) => clean(p.textContent))
      : [];

    const statRows = [];
    const st = info && info.querySelector('#StatTable');
    if (st) {
      [...st.querySelectorAll('tr')].forEach((tr) => {
        const v = tr.querySelector('td.value');
        const img = tr.querySelector('img');
        const val = clean(v ? v.textContent : '');
        if (val) statRows.push({'icon': img ? img.getAttribute('alt') || iconName(img.getAttribute('src')) : '?', 'value': val.replace(/^:\s*/, '')});
      });
    }

    const rewardRows = [];
    const rt = info && info.querySelector('#RewardTable');
    if (rt) {
      [...rt.querySelectorAll('tr')].forEach((tr) => {
        const v = tr.querySelector('td.value');
        const img = tr.querySelector('img');
        const val = clean(v ? v.textContent : '');
        if (val) rewardRows.push({'icon': img ? img.getAttribute('alt') || iconName(img.getAttribute('src')) : '', 'value': val.replace(/^:\s*/, '')});
      });
    }

    const effectHtml = info ? [...info.querySelectorAll('.effectOutcome')].map((e) => e.innerHTML.trim()).filter(Boolean) : [];

    // every image inside the card text, so the cleaner knows what to name
    if (info) {
      [...info.querySelectorAll('img')].forEach((img) => {
        const n = img.getAttribute('alt') || iconName(img.getAttribute('src'));
        inventory[n] = (inventory[n] || 0) + 1;
      });
    }

    return {
      slug,
      name: clean((d.querySelector('h1') || {}).textContent),
      set: ps[0] || '',
      type: ps[1] || '',
      stat_rows: statRows,
      reward_rows: rewardRows,
      effect_html: effectHtml,
      display: clean(display ? display.innerText : ''),
      raw: clean(info ? info.innerText : ''),
    };
  };

  const rows = new Array(list.length);
  const failed = [];
  let fetched = 0;
  let aborted = false;
  const worker2 = async (start) => {
    for (let i = start; i < list.length && !aborted; i += CONC) {
      try {
        rows[i] = extract(list[i], dom(await grab(list[i])));
      } catch (e) {
        failed.push(list[i] + ' :: ' + e.message);
        if (e.message.indexOf('challenge') === 0) aborted = true;
      }
      fetched++;
      if (fetched % 50 === 0) console.log('fetch', fetched, '/', list.length);
      await sleep(90);
    }
  };
  await Promise.all(Array.from({ length: CONC }, (_, k) => worker2(k)));

  const got = rows.filter(Boolean);
  console.log('fetched', got.length, '| failed', failed.length);
  if (failed.length) console.table(failed);

  const blob = new Blob([JSON.stringify(got, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'four_souls_html_n' + got.length + '.json';
  a.click();
  console.log('icons seen:', inventory);
})();
