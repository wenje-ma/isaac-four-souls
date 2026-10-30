// Dump every article title of the Isaac wiki, so card names can be checked
// against the game's own vocabulary offline.
//
// Paste into the Chrome DevTools console while on https://bindingofisaacrebirth.wiki.gg/
// with the site open in the same tab. It walks Special:AllPages through the
// wiki's own API, then downloads isaac_wiki_titles.json.
//
// Robots rules keep a crawler out of this site, so this runs in your own
// browser session, on the pages you already have open.

(async () => {
  const LIMIT = 500;
  const PAUSE = 400;
  const titles = [];
  let cont = null;
  let round = 0;

  try {
    do {
      const q = new URLSearchParams({
        action: 'query',
        list: 'allpages',
        apnamespace: '0',
        aplimit: String(LIMIT),
        format: 'json',
        formatversion: '2',
      });
      if (cont) q.set('apcontinue', cont);
      const r = await fetch('/api.php?' + q.toString(), { credentials: 'include' });
      if (!r.ok) throw new Error('http ' + r.status);
      const j = await r.json();
      for (const p of j.query.allpages) titles.push(p.title);
      cont = j.continue ? j.continue.apcontinue : null;
      round++;
      console.log('round', round, 'titles', titles.length, cont ? 'more' : 'done');
      await new Promise((res) => setTimeout(res, PAUSE));
    } while (cont);
  } catch (e) {
    console.error('stopped:', e.message, 'collected so far:', titles.length);
  }

  const blob = new Blob([JSON.stringify(titles)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'isaac_wiki_titles.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  console.log('saved isaac_wiki_titles.json with', titles.length, 'titles');
})();
