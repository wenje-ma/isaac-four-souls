// Two character cards missed by the previous contact sheets.
// Their art filenames do not contain the slug, so instead of matching by
// name this loads every image on the page and keeps the largest one.

(async () => {
  const TARGETS = ['/cards/mew-stacy-704891/', '/cards/nen-isaac/'];
  const CELL_W = 640;
  const LABEL_H = 26;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const dom = (h) => new DOMParser().parseFromString(h, 'text/html');

  const loadImg = (u) => new Promise((resolve, reject) => {
    const im = new Image();
    im.onload = () => resolve(im);
    im.onerror = () => reject(new Error('img fail ' + u));
    im.src = u;
  });

  const picked = [];
  for (const s of TARGETS) {
    const r = await fetch(s, { credentials: 'include' });
    const d = dom(await r.text());
    const box = d.querySelector('#CardDisplay') || d;
    const urls = [...new Set([...box.querySelectorAll('img')]
      .map((im) => im.getAttribute('data-src') || im.getAttribute('src') || '')
      .filter((u) => u && /\.(png|jpe?g|webp)$/i.test(u))
      .map((u) => new URL(u, location.href).href))];
    console.log(s, 'candidates', urls.length);
    urls.slice(0, 8).forEach((u) => console.log('   ', u));

    let best = null;
    for (const u of urls) {
      try {
        const im = await loadImg(u);
        if (!best || im.naturalWidth * im.naturalHeight > best.im.naturalWidth * best.im.naturalHeight) {
          best = { url: u, im };
        }
      } catch (e) {}
      await sleep(120);
    }
    if (best) {
      console.log('  picked', best.url, best.im.naturalWidth, best.im.naturalHeight);
      picked.push({ slug: s.replace('/cards/', '').replace(/\/$/, ''), im: best.im });
    } else {
      console.log('  nothing loaded');
    }
  }

  const cellH = LABEL_H + Math.round(CELL_W * 0.75);
  const cv = document.createElement('canvas');
  cv.width = CELL_W;
  cv.height = Math.max(1, picked.length) * cellH;
  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, cv.width, cv.height);
  ctx.fillStyle = '#000';

  picked.forEach((p, i) => {
    const y = i * cellH;
    ctx.font = '18px sans-serif';
    ctx.fillText(p.slug, 8, y + 19);
    const w = p.im.naturalWidth;
    const h = p.im.naturalHeight;
    ctx.drawImage(p.im, 0, Math.floor(h * 0.45), w, Math.ceil(h * 0.55),
      0, y + LABEL_H, CELL_W, cellH - LABEL_H);
  });

  cv.toBlob((blob) => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'start_items_missing2.png';
    document.body.appendChild(a);
    a.click();
    a.remove();
  }, 'image/png');
  console.log('saved start_items_missing2.png', picked.length);
})();
