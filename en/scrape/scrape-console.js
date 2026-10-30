// v4: real selectors from the live DOM.
//   stats   -> table#StatTable rows (td.value + icon img[alt])
//   effect  -> #CardInfo div.effectOutcome
//   rewards -> #CardInfo table#RewardTable (td.value + icon alt)
//   display -> whole #CardDisplay text, kept as a lossless fallback
// Every card is fetched with up to 2 retries on transient errors.

const START = 0;
const LIMIT = 0;

(async () => {
  const CONC = 3;
  const RETRY = 2;
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
        await sleep(400 * (i + 1));
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

  const extract = (slug, d) => {
    const info = d.querySelector('#CardInfo');
    const display = d.querySelector('#CardDisplay');
    const ps = info && info.querySelector('#OriginSet')
      ? [...info.querySelectorAll('#OriginSet p')].map((p) => clean(p.textContent))
      : [];

    const stats = [];
    const st = info && info.querySelector('#StatTable');
    if (st) {
      [...st.querySelectorAll('tr')].forEach((tr) => {
        const v = tr.querySelector('td.value');
        const img = tr.querySelector('img');
        const val = clean(v ? v.textContent : '');
        if (val) stats.push((img && img.getAttribute('alt') ? img.getAttribute('alt') : '?') + ':' + val);
      });
    }

    const rewards = [];
    const rt = info && info.querySelector('#RewardTable');
    if (rt) {
      [...rt.querySelectorAll('tr')].forEach((tr) => {
        const v = tr.querySelector('td.value');
        const img = tr.querySelector('img');
        const val = clean(v ? v.textContent : '');
        if (val) rewards.push(val + ' ' + (img && img.getAttribute('alt') ? img.getAttribute('alt') : ''));
      });
    }

    const effects = info ? [...info.querySelectorAll('.effectOutcome')].map((e) => clean(e.textContent)).filter(Boolean) : [];

    return {
      slug: slug,
      name: clean((d.querySelector('h1') || {}).textContent),
      set: ps[0] || '',
      type: ps[1] || '',
      stats: stats.join('; '),
      effect: effects.join(' '),
      rewards: rewards.join('; '),
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

  const ok = rows.filter(Boolean);
  console.log('fetched', ok.length, '| failed', failed.length, aborted ? '| ABORTED' : '');
  if (failed.length) console.log(failed.slice(0, 8));

  const save = (name, text, mime) => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: mime }));
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const fields = ['slug', 'name', 'set', 'type', 'stats', 'effect', 'rewards', 'display'];
  const esc = (v) => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
  const csv = [fields.join(',')]
    .concat(ok.map((r) => fields.map((f) => esc(r[f])).join(',')))
    .join('\r\n');
  const tag = 'v4_n' + ok.length;
  save('four_souls_' + tag + '.json', JSON.stringify(ok, null, 1), 'application/json');
  save('four_souls_' + tag + '.csv', '\ufeff' + csv, 'text/csv');
  console.log('saved four_souls_' + tag + '.json / .csv');
})();
