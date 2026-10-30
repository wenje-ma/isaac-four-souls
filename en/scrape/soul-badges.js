// Export the card front images of the 169 cards that have no reward box, as
// contact sheets, so the soul-value badge drawn on the art can be read by eye.
//
// Paste into the Chrome DevTools console while on https://foursouls.com/ with
// the site open. Downloads soul_badges_01.png, _02.png, ... one sheet per 12
// cards, each cell labelled with its slug.
//
// v2 logs every card and gives each image 6 seconds to load, so a hang shows up
// as a line instead of silence.

(async () => {
  const SLUGS = [
    'b2-blue_baby','b2-cain','b2-eve','b2-judas','b2-lazarus','b2-lilith','b2-maggy','b2-samson',
    'b2-the_forgotten','g2-apollyon','g2-azazel','g2-the_keeper','nen-isaac','r-bethany','r-eden',
    'r-jacob_and_esau','anni-dataminer','anni-booster_pack','aa-godhead','aa-guppys_paw',
    'b2-blood_lust','b2-book_of_belial','b2-the_curse','b2-the_d6','b2-yum_heart','b2-belly_button',
    'b2-bobs_brain','b2-breakfast','b2-champion_belt','b2-charged_baby','b2-curse_of_the_tower',
    'b2-dads_lost_coin','b2-dinner','b2-dry_baby','b2-empty_vessel','b2-finger','b2-goat_head',
    'b2-guppys_collar','b2-ipecac','b2-meat','b2-moms_box','b2-moms_razor','b2-monstros_tooth',
    'b2-polydactyly','b2-restock','b2-sacred_heart','b2-spider_mod','b2-synthoil','b2-tarot_cloth',
    'b2-the_blue_map','b2-the_compass','b2-the_d10','b2-the_dead_cat','b2-the_habit','b2-the_map',
    'b2-broken_ankh','b2-cains_eye','b2-curved_horn','b2-golden_horseshoe','b2-guppys_hairball',
    'fsp2-20_20','fsp2-black_candle','fsp2-distant_admiration','fsp2-head_of_krampus','fsp2-libra',
    'fsp2-mutant_spider','fsp2-red_candle','fsp2-smart_fly','fsp2-gimpy','fsp2-forget_me_now',
    'fsp2-athame','fsp2-abaddon','fsp2-cursed_eye','fsp2-daddy_long_legs','fsp2-euthanasia',
    'fsp2-guppys_eye','fsp2-hourglass','fsp2-lard','fsp2-moms_eye_shadow','fsp2-polyphemus',
    'fsp2-rubber_cement','fsp2-telepathy_for_dummies','fsp2-the_wiz','fsp2-aaa_battery',
    'fsp2-poker_chip','fsp2-tape_worm','fsp2-the_left_hand','gf-g_fuel-red','gf-isaacs_tears',
    'gf-brimstone','gi-lil_gish','g2-crooked_penny','g2-i_cant_believe_its_not_butter_bean',
    'g2-lemon_mishap','g2-ouija_board','g2-the_bible','g2-the_butter_bean','g2-holy_mantle',
    'g2-lord_of_the_pit','g2-void','g2-plan_c','g2-dads_key','g2-succubus','g2-9_volt',
    'g2-guppys_tail','g2-infamy','g2-moms_knife','g2-more_options','g2-placenta','g2-skeleton_key',
    'g2-soy_milk','g2-the_missing_page','g2-cancer','g2-pink_eye','nen-guppys-head',
    'p-mystery_gift','p-dads_ring','p-lump_of_coal','p-pyromaniac','p-short_fuse','r-birthright',
    'r-book_of_the_dead','r-eternal_d6','r-friendly_ball','r-marbles','r-member_card','r-red_key',
    'r-undefined','r-x_ray_vision','r-abyss','r-berserk','r-gello','r-hemoptysis','r-lemegeton',
    'r-spindown_dice','r-sumptorium','r-mama_mega','r-r_key','r-the_clicker','r-battery_pack',
    'r-car_battery','r-abel','r-ball_of_bandages','r-blood_puppy','r-chocolate_milk','r-fire_mind',
    'r-gnawed_leaf','r-halo_of_flies','r-lodestone','r-lunch','r-moms_bottle_of_pills',
    'r-spelunker_hat','r-bag_lunch','r-broken_remote','r-callus','r-golden_trinket',
    'r-rib_of_greed','r-tick','ret-1_up','soi-isaacs_last_will','soi-telekinesis','soi-the_monster',
    'soi-ball_of_tar','soi-magic_mushroom','soi-karma','soi-found_soul','t-epic_fetus','t-dead_eye',
    't-marked',
  ];

  const COLS = 4, ROWS = 3, W = 300, H = 420, LBL = 20;
  const PER = COLS * ROWS;
  const PAUSE = 180;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  console.log('start, cards:', SLUGS.length);

  let sheet = 0, canvas = null, ctx = null, slot = 0;
  const missing = [];

  function openSheet() {
    sheet++;
    canvas = document.createElement('canvas');
    canvas.width = COLS * W;
    canvas.height = ROWS * (H + LBL);
    ctx = canvas.getContext('2d');
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = '14px monospace';
    ctx.textBaseline = 'top';
    slot = 0;
  }

  function saveSheet() {
    if (!canvas) return;
    const c = canvas;
    canvas = null;
    c.toBlob((b) => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(b);
      a.download = 'soul_badges_' + String(sheet).padStart(2, '0') + '.png';
      document.body.appendChild(a);
      a.click();
      a.remove();
    }, 'image/png');
    console.log('sheet', sheet, 'saved');
  }

  function firstImage(html) {
    const m = html.match(/https?:\/\/[^"'\s>]+wp-content\/uploads[^"'\s>]+\.(?:jpg|jpeg|png)/gi) || [];
    const cleaned = m.filter((u) => !/logo|icon|avatar|thumb|placeholder/i.test(u));
    return cleaned.length ? cleaned[0] : null;
  }

  function loadImage(url) {
    return new Promise((res, rej) => {
      const im = new Image();
      const t = setTimeout(() => rej(new Error('image timeout')), 6000);
      im.onload = () => { clearTimeout(t); res(im); };
      im.onerror = () => { clearTimeout(t); rej(new Error('image error')); };
      im.src = url;
    });
  }

  openSheet();
  for (let i = 0; i < SLUGS.length; i++) {
    const slug = SLUGS[i];
    try {
      const r = await fetch('/cards/' + slug + '/', { credentials: 'include' });
      const html = await r.text();
      const url = firstImage(html);
      console.log(i, slug, 'status', r.status, 'html', html.length, 'img', url ? 'yes' : 'no');
      if (!url) throw new Error('no image url');
      const im = await loadImage(url);
      const col = slot % COLS, row = Math.floor(slot / COLS);
      const x = col * W, y = row * (H + LBL);
      ctx.fillStyle = '#fff';
      ctx.fillRect(x, y, W, H + LBL);
      ctx.drawImage(im, x, y + LBL, W, H);
      ctx.fillStyle = '#000';
      ctx.fillText(slug, x + 4, y + 3);
      slot++;
      if (slot === PER) {
        saveSheet();
        if (i + 1 < SLUGS.length) openSheet();
      }
    } catch (e) {
      missing.push(slug);
      console.warn('fail', slug, e.message);
    }
    await sleep(PAUSE);
  }
  if (canvas && slot) saveSheet();
  console.log('done. missing:', missing.length, missing);
})();
