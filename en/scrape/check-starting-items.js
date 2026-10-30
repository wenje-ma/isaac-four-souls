// Second pass over the 113 character cards: crop only the bottom band where
// "STARTING ITEM: ..." is printed, and blow it up bigger than the first pass.
// The point is to re-read the line at a different scale and compare it against
// data/starting_items.csv, so a misread on the first pass shows up as a diff.

(async () => {
  const CONC = 4;
  const CELL_W = 520;
  const LABEL_H = 26;
  const COLS = 3;
  const ROWS = 4;
  const PER = COLS * ROWS;
  // the line sits low on the card face; keep the bottom fifth and a little air
  const CROP_FROM = 0.66;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const dom = (h) => new DOMParser().parseFromString(h, 'text/html');

  const grab = async (u) => {
    const r = await fetch(u, { credentials: 'include' });
    if (!r.ok) throw new Error(r.status + ' ' + u);
    return r.text();
  };

  const idx = dom(await grab('/cards/'));
  const origins = [...new Set([...idx.querySelectorAll('a')]
    .map((a) => a.getAttribute('href') || '')
    .filter((h) => h.indexOf('origin=') > -1)
    .map((h) => new URL(h, location.href).searchParams.get('origin')))]
    .filter(Boolean);

  const urls = ['/card-search/?card_type=character'].concat(
    origins.map((o) => '/card-search/?origin=' + o + '&card_type=character'));
  const slugs = new Set();
  for (const u of urls) {
    try {
      const d = dom(await grab(u));
      d.querySelectorAll('a').forEach((a) => {
        try {
          const p = new URL(a.getAttribute('href') || '', location.href).pathname;
          if (p.indexOf('/cards/') === 0 && p !== '/cards/') slugs.add(p);
        } catch (e) {}
      });
    } catch (e) {
      console.warn('enum fail', u, e.message);
    }
    await sleep(80);
  }
  const list = [...slugs].sort();
  console.log('character slugs', list.length);

  const art = {};
  let done = 0;
  const worker = async (start) => {
    for (let i = start; i < list.length; i += CONC) {
      const s = list[i];
      try {
        const d = dom(await grab(s));
        const base = s.replace('/cards/', '').replace(/\/$/, '');
        const cands = [...d.querySelectorAll('#CardDisplay img')]
          .map((im) => im.getAttribute('data-src') || im.getAttribute('src') || '')
          .filter((u) => u && /\.(png|jpe?g)$/i.test(u) && u.indexOf('CardBack') < 0 && u.indexOf(base) > -1)
          .map((u) => new URL(u, location.href).href);
        if (cands.length) art[s] = cands[0];
      } catch (e) {
        console.warn('page fail', s, e.message);
      }
      done++;
      if (done % 20 === 0) console.log('pages', done, '/', list.length);
      await sleep(90);
    }
  };
  await Promise.all(Array.from({ length: CONC }, (_, k) => worker(k)));
  console.log('art urls', Object.keys(art).length);

  const loadImg = (u) => new Promise((resolve, reject) => {
    const im = new Image();
    im.onload = () => resolve(im);
    im.onerror = () => reject(new Error('img fail ' + u));
    im.src = u;
  });

  const loadArt = async (u) => {
    let last;
    for (let i = 0; i < 3; i++) {
      try {
        return await loadImg(u);
      } catch (e) {
        last = e;
        await sleep(700 * (i + 1));
      }
    }
    throw last;
  };

  const items = Object.keys(art);
  let sheet = 0;
  for (let i = 0; i < items.length; i += PER) {
    sheet++;
    const chunk = items.slice(i, i + PER);
    const cellH = LABEL_H + Math.round(CELL_W * 0.34);
    const cv = document.createElement('canvas');
    cv.width = COLS * CELL_W;
    cv.height = ROWS * cellH;
    const ctx = cv.getContext('2d');
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, cv.width, cv.height);

    for (let k = 0; k < chunk.length; k++) {
      const slug = chunk[k];
      const col = k % COLS;
      const row = Math.floor(k / COLS);
      const x = col * CELL_W;
      const y = row * cellH;
      ctx.fillStyle = '#000';
      ctx.font = '17px sans-serif';
      ctx.fillText(slug.replace('/cards/', ''), x + 6, y + 19);
      ctx.strokeStyle = '#bbb';
      ctx.strokeRect(x, y + LABEL_H, CELL_W, cellH - LABEL_H);
      try {
        const bmp = await loadArt(art[slug]);
        const w = bmp.naturalWidth;
        const h = bmp.naturalHeight;
        ctx.drawImage(bmp, 0, Math.floor(h * CROP_FROM), w, Math.ceil(h * (1 - CROP_FROM)),
          x, y + LABEL_H, CELL_W, cellH - LABEL_H);
      } catch (e) {
        ctx.fillText('IMG FAIL ' + e.message.slice(0, 40), x + 6, y + LABEL_H + 24);
      }
      await sleep(150);
    }

    await new Promise((res) => cv.toBlob((blob) => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'start_items_check_' + sheet + '.png';
      document.body.appendChild(a);
      a.click();
      a.remove();
      res();
    }, 'image/png'));
    await sleep(400);
    console.log('sheet', sheet, 'done', chunk.length);
  }
  console.log('total sheets', Math.ceil(items.length / PER));
})();
