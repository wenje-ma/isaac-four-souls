// Dump the wiki's category membership plus the link lists of the hub pages,
// so the printed cards can be compared against what the game actually contains.
//
// Paste into the Chrome DevTools console while on https://bindingofisaacrebirth.wiki.gg/
// with the site open in the same tab. Downloads isaac_wiki_categories.json.
//
// Run 2 fixes two things from run 1: `Category:Items` is empty because this wiki
// files items elsewhere, and `allcategories` crashed on an undefined name. So
// this version dumps every category name with its size first, fetches members
// for the ones that look like content lists, and also reads the link list of
// the Items / Enemies / Bosses / Trinkets / Characters hub pages as a fallback.

(async () => {
  const LIMIT = 500;
  const PAUSE = 350;
  const KEY = /^(items?|active items?|passive items?|collectibles?|trinkets?|enemies|enemy|monsters?|bosses?|boss|characters?|challenges?|rooms?|transformations?|cards?|runes?|pickups?|playable characters?)$/i;

  const sleep = () => new Promise((res) => setTimeout(res, PAUSE));

  async function api(params) {
    const q = new URLSearchParams(Object.assign({ format: 'json', formatversion: '2' }, params));
    const r = await fetch('/api.php?' + q.toString(), { credentials: 'include' });
    if (!r.ok) throw new Error('http ' + r.status);
    return r.json();
  }

  async function members(cat) {
    const out = [];
    let cont = null;
    do {
      const p = {
        action: 'query', list: 'categorymembers', cmtitle: 'Category:' + cat,
        cmlimit: String(LIMIT), cmnamespace: '0',
      };
      if (cont) p.cmcontinue = cont;
      const j = await api(p);
      const list = (j.query && j.query.categorymembers) || [];
      for (const m of list) out.push(m.title);
      cont = j['continue'] ? j['continue'].cmcontinue : null;
      await sleep();
    } while (cont);
    return out;
  }

  async function links(page) {
    const j = await api({ action: 'parse', page, prop: 'links', redirects: '1' });
    const l = (j.parse && j.parse.links) || [];
    return l.filter((x) => x.ns === 0).map((x) => x['*'] || x.title || '');
  }

  // 1. every category name, with its size
  const cats = [];
  let cont = null;
  do {
    const p = { action: 'query', list: 'allcategories', aclimit: String(LIMIT), acprop: 'size' };
    if (cont) p.accontinue = cont;
    const j = await api(p);
    for (const c of j.query.allcategories) cats.push({ name: c.category || c['*'] || '', size: c.size || 0 });
    cont = j['continue'] ? j['continue'].accontinue : null;
    await sleep();
  } while (cont);
  console.log('categories seen:', cats.length);

  // 2. members of the categories that look like content lists
  const wanted = cats.filter((c) => KEY.test(c.name));
  const result = {};
  const report = [];
  for (const c of wanted) {
    try {
      const list = await members(c.name);
      result[c.name] = list;
      report.push({ cat: c.name, size: c.size, got: list.length });
      console.log(c.name, list.length);
    } catch (e) {
      report.push({ cat: c.name, size: c.size, got: -1 });
      console.warn(c.name, 'failed:', e.message);
    }
  }

  // 3. hub page link lists, as a fallback for anything the categories miss
  const hubs = ['Items', 'Trinkets', 'Enemies', 'Bosses', 'Characters', 'Challenges'];
  const hubData = {};
  for (const h of hubs) {
    try {
      hubData[h] = await links(h);
      console.log('hub', h, hubData[h].length);
    } catch (e) {
      console.warn('hub', h, 'failed:', e.message);
    }
  }

  const payload = { categories: result, report, hub_links: hubData, all_categories: cats };
  const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'isaac_wiki_categories.json';
  document.body.appendChild(a);
  a.click();
  a.remove();

  console.table(report);
  console.log('saved isaac_wiki_categories.json');
})();
