(() => {
  const $ = s => document.querySelector(s);
  const root = document.documentElement;

  try { root.dataset.theme = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); }
  catch { root.dataset.theme = 'light'; }
  $('#theme').onclick = () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('theme', root.dataset.theme); } catch {}
  };


  // the X button of type="search" only clears the text; reload the list when a search was active
  $('#searchInput').addEventListener('input', e => {
    if (!e.target.value && new URLSearchParams(location.search).get('q')) e.target.form.submit();
  });

  const flash = (b, msg) => { const o = b.textContent; b.textContent = msg; setTimeout(() => b.textContent = o, 1200); };
  const save = (text, name) => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'application/x-pem-file' }));
    a.download = name; a.click(); URL.revokeObjectURL(a.href);
  };

  const drawer = $('#drawer'), back = $('#backdrop'); let cur = null;
  function open(r) {
    cur = r; $('#dTitle').textContent = r.dataset.domain;
    const pill = document.createElement('span');
    pill.className = 'pill ' + r.dataset.status; pill.textContent = r.dataset.label;
    $('#dSub').replaceChildren(pill);
    $('#dBody').replaceChildren(r.querySelector('template').content.cloneNode(true));
    drawer.classList.add('open'); back.classList.add('open'); drawer.setAttribute('aria-hidden', 'false'); $('#dClose').focus();
  }
  function close() { drawer.classList.remove('open'); back.classList.remove('open'); drawer.setAttribute('aria-hidden', 'true'); }

  $('#certTable tbody').onclick = e => {
    const r = e.target.closest('tr[data-domain]'); if (!r) return;
    const c = e.target.closest('.caid');
    if (c && r.dataset.ca) { navigator.clipboard.writeText(r.dataset.ca); flash(c, 'Copied'); return; }
    open(r);
  };
  $('#dClose').onclick = close; back.onclick = close;
  drawer.onclick = e => {
    const b = e.target.closest('button[data-act]'); if (!b) return;
    const box = b.closest('.pem'), text = box.querySelector('pre').textContent;
    if (b.dataset.act === 'copy') { navigator.clipboard.writeText(text); flash(b, 'Copied'); }
    else save(text, `${cur.dataset.domain}-${box.dataset.name}.pem`);
  };
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') close();
    if (e.key === '/' && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); $('#searchInput').focus(); }
  });
})();