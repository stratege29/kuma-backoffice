# -*- coding: utf-8 -*-
"""
Campaign Builder - Centre de Notifications (refonte)
====================================================

Parcours guide en 5 etapes : Audience -> Message -> Programmation -> Verif -> Resultats.

Page 100% front-end (HTML/CSS/JS) qui reutilise les endpoints existants :
  GET  /api/notifications-v2/lists
  GET  /api/notifications-v2/templates
  POST /api/notifications-v2/preview
  POST /api/notifications-v2/send
  POST /api/notifications-v2/schedule
  GET  /api/notifications-v2/scheduled
  POST /api/notifications-v2/scheduled/{id}/cancel
  POST /api/notifications-v2/scheduled/{id}/send-now
  GET  /api/notifications-v2/history

Chaine simple (pas de f-string) -> aucune accolade a echapper.
"""


def generate_campaign_builder_page(firebase_initialized: bool = False) -> str:
    notice = ('<div class="cb-alert ok">Systeme de notifications connecte</div>'
              if firebase_initialized else
              '<div class="cb-alert warn">Firebase deconnecte - fonctionnalites limitees</div>')
    return _PAGE.replace('__FIREBASE_NOTICE__', notice)


_PAGE = r'''
<style>
  .cb { color: #111827; }
  .cb h2 { margin: 0 0 4px; }
  .cb-alert { padding: 10px 14px; border-radius: 8px; font-size: 13px; margin: 10px 0 18px; }
  .cb-alert.ok { background: #dcfce7; color: #166534; }
  .cb-alert.warn { background: #fef3c7; color: #92400e; }

  .cb-steps { display: flex; gap: 6px; margin-bottom: 8px; }
  .cb-step { flex: 1; display: flex; align-items: center; gap: 8px; padding: 10px 12px; border: 1px solid #e5e7eb;
             border-radius: 10px; background: #fff; cursor: pointer; color: #6b7280; font-size: 13px; }
  .cb-step .num { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
                  background: #f3f4f6; color: #6b7280; font-weight: 600; font-size: 12px; flex-shrink: 0; }
  .cb-step.on { border-color: #FF6B35; color: #111827; box-shadow: 0 1px 4px rgba(255,107,53,0.15); }
  .cb-step.on .num { background: #FF6B35; color: #fff; }
  .cb-step.done .num { background: #22c55e; color: #fff; }

  .cb-context { display: flex; flex-wrap: wrap; gap: 14px; background: #f9fafb; border: 1px solid #eef0f2; border-radius: 10px;
                padding: 10px 14px; margin-bottom: 16px; font-size: 13px; color: #374151; }
  .cb-context b { color: #111827; font-weight: 600; }
  .cb-context .muted { color: #9ca3af; }

  .cb-panel { display: none; }
  .cb-panel.on { display: block; }
  .cb-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; margin-bottom: 14px; }
  .cb-card h3 { margin: 0 0 12px; font-size: 1.05rem; }
  .cb-hint { color: #6b7280; font-size: 13px; margin: 0 0 12px; }

  .cb-search { width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; margin-bottom: 12px; box-sizing: border-box; }
  .cb-group-title { font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: #9ca3af; margin: 14px 0 6px; }
  .cb-seg { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 12px; border: 1px solid #e5e7eb;
            border-radius: 10px; margin-bottom: 8px; cursor: pointer; background: #fff; }
  .cb-seg:hover { border-color: #d1d5db; background: #fafafa; }
  .cb-seg.sel { border-color: #FF6B35; background: #fff7ed; }
  .cb-seg .left { display: flex; align-items: center; gap: 10px; min-width: 0; }
  .cb-seg .nm { font-weight: 500; }
  .cb-seg .desc { color: #9ca3af; font-size: 12px; }
  .cb-seg .right { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #6b7280; white-space: nowrap; }
  .cb-pill { font-size: 11px; padding: 2px 8px; border-radius: 999px; font-weight: 600; }
  .cb-pill.urgent { background: #fee2e2; color: #991b1b; }
  .cb-pill.high { background: #ffedd5; color: #9a3412; }
  .cb-count { background: #eef2ff; color: #3730a3; font-weight: 600; padding: 2px 8px; border-radius: 999px; }

  .cb-seg-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
  .cb-toggle { display: flex; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; margin-bottom: 14px; }
  .cb-toggle button { flex: 1; padding: 10px; border: none; background: #f9fafb; cursor: pointer; font-weight: 500; color: #374151; }
  .cb-toggle button.on { background: #FF6B35; color: #fff; }
  .cb-chip { padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 999px; background: #fff; cursor: pointer; font-size: 13px; color: #374151; }
  .cb-chip.on { background: #fff7ed; border-color: #FF6B35; color: #9a3412; }

  .cb-grid2 { display: grid; grid-template-columns: 1fr 260px; gap: 18px; }
  @media (max-width: 900px) { .cb-grid2 { grid-template-columns: 1fr; } }

  .cb-tpl-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; max-height: 420px;
                 overflow-y: auto; padding: 4px; background: #fafafa; border: 1px solid #eef0f2; border-radius: 10px; }
  .cb-tpl { padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; cursor: pointer; }
  .cb-tpl:hover { border-color: #FF6B35; }
  .cb-tpl.sel { border-color: #FF6B35; background: #fff7ed; }
  .cb-tpl .th { display: flex; align-items: center; gap: 6px; font-weight: 500; font-size: 13px; }
  .cb-tpl .tp { color: #6b7280; font-size: 11px; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
  .cb-tpl .ab { font-size: 10px; color: #9a3412; background: #ffedd5; border-radius: 4px; padding: 0 4px; margin-left: auto; }

  .cb-field { margin-bottom: 12px; }
  .cb-field label { display: block; font-weight: 600; font-size: 13px; margin-bottom: 5px; color: #374151; }
  .cb-field input, .cb-field textarea, .cb-field select { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px;
              font-size: 14px; font-family: inherit; box-sizing: border-box; }
  .cb-field textarea { min-height: 90px; resize: vertical; }
  .cb-vars { font-size: 12px; color: #6b7280; }
  .cb-vars code { background: #f3f4f6; padding: 1px 5px; border-radius: 4px; cursor: pointer; }

  .cb-phone { background: #111827; border-radius: 18px; padding: 14px 10px; position: sticky; top: 12px; }
  .cb-phone .t { color: #9ca3af; font-size: 11px; text-align: center; margin-bottom: 8px; }
  .cb-notif { background: #fff; border-radius: 10px; padding: 10px; display: flex; gap: 8px; }
  .cb-notif .cb-avatar { width: 38px; height: 38px; border-radius: 9px; object-fit: cover; flex-shrink: 0; background: #fff; }
  .cb-notif .tt { font-weight: 600; font-size: 12px; color: #111827; }
  .cb-notif .bb { font-size: 11px; color: #4b5563; margin-top: 2px; }

  .cb-days { display: flex; gap: 6px; flex-wrap: wrap; }
  .cb-days label { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 8px; cursor: pointer; }

  .cb-recap { display: grid; gap: 10px; }
  .cb-recap .row { display: flex; justify-content: space-between; gap: 10px; padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 10px; }
  .cb-recap .row .k { color: #6b7280; font-size: 13px; }
  .cb-recap .row .v { font-weight: 500; text-align: right; }

  .cb-nav { display: flex; justify-content: space-between; margin-top: 6px; }
  .cb-btn { padding: 10px 18px; border-radius: 10px; border: 1px solid #d1d5db; background: #fff; color: #374151; cursor: pointer; font-size: 14px; }
  .cb-btn:hover { background: #f3f4f6; }
  .cb-btn.primary { background: #FF6B35; border-color: #FF6B35; color: #fff; }
  .cb-btn.primary:hover { background: #e85d2a; }
  .cb-btn.green { background: #22c55e; border-color: #22c55e; color: #fff; }
  .cb-btn:disabled { opacity: .5; cursor: not-allowed; }

  .cb-tabs { display: flex; gap: 8px; margin-bottom: 12px; }
  .cb-status { font-size: 11px; padding: 2px 10px; border-radius: 999px; font-weight: 600; }
  .cb-status.queued { background: #dbeafe; color: #1e40af; }
  .cb-status.sending { background: #fef3c7; color: #92400e; }
  .cb-status.sent { background: #dcfce7; color: #166534; }
  .cb-status.failed { background: #fee2e2; color: #991b1b; }
  .cb-status.canceled { background: #e5e7eb; color: #4b5563; }
  .cb-htable { width: 100%; border-collapse: collapse; font-size: 13px; }
  .cb-htable th, .cb-htable td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #eef0f2; }
  .cb-htable th { color: #6b7280; background: #f9fafb; font-weight: 600; }
  .cb-pending { color: #9ca3af; font-style: italic; }
</style>

<div class="cb">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
    <h2>🔔 Nouvelle campagne push</h2>
    <button class="cb-btn" onclick="cbGoto(5)">📋 Campagnes programmées</button>
  </div>
  __FIREBASE_NOTICE__

  <div class="cb-steps" id="cb-steps"></div>
  <div class="cb-context" id="cb-context"></div>

  <!-- STEP 1 : AUDIENCE -->
  <div class="cb-panel" data-step="1">
    <div class="cb-card">
      <h3>1. Choisis ton audience</h3>
      <p class="cb-hint">Sélectionne le segment d'utilisateurs à qui envoyer la notification.</p>
      <input class="cb-search" id="cb-list-search" placeholder="Rechercher un segment..." oninput="cbRenderLists()">
      <div id="cb-lists"><div class="cb-hint">Chargement des segments...</div></div>
    </div>
    <div class="cb-nav"><span></span><button class="cb-btn primary" id="cb-next-1" onclick="cbGoto(2)" disabled>Suivant →</button></div>
  </div>

  <!-- STEP 2 : MESSAGE -->
  <div class="cb-panel" data-step="2">
    <div class="cb-card">
      <h3>2. Compose ton message</h3>
      <div class="cb-grid2">
        <div>
          <div class="cb-toggle" id="cb-channel">
            <button class="on" onclick="cbSetChannel('push')">🔔 Push</button>
            <button onclick="cbSetChannel('email')">📧 Email</button>
          </div>
          <div id="cb-push-block">
            <div class="cb-toggle" id="cb-mode">
              <button class="on" onclick="cbSetMode('template')">📋 Template</button>
              <button onclick="cbSetMode('custom')">✏️ Personnalisé</button>
            </div>
            <div id="cb-template-block">
              <div class="cb-seg-row" id="cb-tpl-cats"></div>
              <div class="cb-tpl-grid" id="cb-templates"><div class="cb-hint">Chargement...</div></div>
              <div id="cb-tpl-edit" style="display:none; margin-top:14px; border-top:1px solid #eef0f2; padding-top:14px;">
                <div class="cb-field"><label>Titre <span style="font-weight:400;color:#9ca3af;">— modifiable</span></label>
                  <input id="cb-tpl-title" oninput="cbTplEdited()"></div>
                <div class="cb-field"><label>Message <span style="font-weight:400;color:#9ca3af;">— modifiable</span></label>
                  <textarea id="cb-tpl-body" oninput="cbTplEdited()"></textarea></div>
                <div class="cb-vars">Variables : <code onclick="cbInsertVar('{child_name}','cb-tpl-body')">{child_name}</code>
                  <code onclick="cbInsertVar('{country}','cb-tpl-body')">{country}</code>
                  <code onclick="cbInsertVar('{streak}','cb-tpl-body')">{streak}</code>
                  <code onclick="cbInsertVar('{days_inactive}','cb-tpl-body')">{days_inactive}</code></div>
                <p class="cb-hint" id="cb-tpl-editnote" style="margin:8px 0 0;"></p>
              </div>
            </div>
            <div id="cb-custom-block" style="display:none;">
              <div class="cb-field"><label>Titre</label><input id="cb-custom-title" oninput="cbUpdatePreview()" placeholder="Ex: 🔥 {child_name}, ta flamme faiblit…"></div>
              <div class="cb-field"><label>Message</label><textarea id="cb-custom-body" oninput="cbUpdatePreview()" placeholder="Ex: Une histoire et ta série repart de plus belle 🌟"></textarea></div>
              <div class="cb-vars">Variables : <code onclick="cbInsertVar('{child_name}')">{child_name}</code>
                <code onclick="cbInsertVar('{country}')">{country}</code>
                <code onclick="cbInsertVar('{streak}')">{streak}</code>
                <code onclick="cbInsertVar('{days_inactive}')">{days_inactive}</code></div>
            </div>
            <label style="display:flex; align-items:center; gap:8px; margin-top:14px; font-size:13px; color:#374151;">
              <input type="checkbox" id="cb-ab" onchange="cbSyncAb()"> Activer l'A/B testing (si le template a des variantes)</label>
          </div>
          <div id="cb-email-block" style="display:none;">
            <div class="cb-field"><label>Sujet</label><input id="cb-email-subject" placeholder="Sujet de l'email"></div>
            <div class="cb-field"><label>Corps (HTML)</label><textarea id="cb-email-body" placeholder="<p>Bonjour {child_name}...</p>"></textarea></div>
            <p class="cb-hint">La programmation est réservée au push ; l'email s'envoie immédiatement.</p>
          </div>
        </div>
        <div>
          <div class="cb-phone" id="cb-preview">
            <div class="t">maintenant</div>
            <div class="cb-notif"><img class="cb-avatar" id="cb-pv-avatar" alt="Kuma"
                 src="https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/app_assets/storyteller/sage_encouragements.png">
              <div style="min-width:0"><div class="tt" id="cb-pv-title">Aperçu</div>
              <div class="bb" id="cb-pv-body">Choisis un template ou écris ton message.</div></div></div>
          </div>
        </div>
      </div>
    </div>
    <div class="cb-nav"><button class="cb-btn" onclick="cbGoto(1)">← Retour</button><button class="cb-btn primary" id="cb-next-2" onclick="cbGoto(3)">Suivant →</button></div>
  </div>

  <!-- STEP 3 : PROGRAMMATION -->
  <div class="cb-panel" data-step="3">
    <div class="cb-card">
      <h3>3. Quand l'envoyer ?</h3>
      <div class="cb-toggle" id="cb-when">
        <button class="on" onclick="cbSetWhen('now')">📤 Envoyer maintenant</button>
        <button onclick="cbSetWhen('schedule')">📅 Programmer</button>
      </div>
      <div id="cb-sched-block" style="display:none;">
        <div class="cb-seg-row">
          <button class="cb-chip on" id="cb-once" onclick="cbSetSchedType('once')">Une seule fois</button>
          <button class="cb-chip" id="cb-recurring" onclick="cbSetSchedType('recurring')">Récurrent</button>
        </div>
        <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:flex-end;">
          <div class="cb-field" id="cb-date-field" style="max-width:200px;"><label>Date</label><input type="date" id="cb-date"></div>
          <div class="cb-field" style="max-width:160px;"><label>Heure</label><input type="time" id="cb-time" value="09:00"></div>
          <div class="cb-field" id="cb-freq-field" style="max-width:200px; display:none;"><label>Fréquence</label>
            <select id="cb-freq" onchange="cbSyncFreq()"><option value="daily">Tous les jours</option><option value="weekly">Chaque semaine</option></select></div>
        </div>
        <div class="cb-field" id="cb-days-field" style="display:none;"><label>Jours</label>
          <div class="cb-days" id="cb-days"></div></div>
        <p class="cb-hint" id="cb-tz-note"></p>
      </div>
      <p class="cb-hint" id="cb-now-note">La notification partira dès la validation à l'étape suivante.</p>
    </div>
    <div class="cb-nav"><button class="cb-btn" onclick="cbGoto(2)">← Retour</button><button class="cb-btn primary" onclick="cbGoto(4)">Suivant →</button></div>
  </div>

  <!-- STEP 4 : VERIF -->
  <div class="cb-panel" data-step="4">
    <div class="cb-card">
      <h3>4. Vérifie et envoie</h3>
      <div class="cb-recap" id="cb-recap"></div>
      <div class="cb-nav" style="margin-top:16px;">
        <button class="cb-btn" onclick="cbGoto(3)">← Retour</button>
        <button class="cb-btn primary" id="cb-final" onclick="cbFinalize()">Envoyer</button>
      </div>
    </div>
  </div>

  <!-- STEP 5 : RESULTATS -->
  <div class="cb-panel" data-step="5">
    <div class="cb-card">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="margin:0;">5. Suivi des campagnes</h3>
        <button class="cb-btn primary" onclick="cbReset()">+ Nouvelle campagne</button>
      </div>
      <div class="cb-tabs" style="margin-top:12px;">
        <button class="cb-chip on" id="cb-tab-queue" onclick="cbResultsTab('queue')">⏳ En file</button>
        <button class="cb-chip" id="cb-tab-hist" onclick="cbResultsTab('hist')">📨 Envoyées</button>
      </div>
      <div id="cb-queue"></div>
      <div id="cb-hist" style="display:none;"></div>
    </div>
  </div>
</div>

<script>
(function(){
  const CB = {
    step: 1,
    lists: [], categories: [], templates: [],
    sel: { list: null, channel: 'push', mode: 'template', template: null, ab: false, fcmOnly: true,
           sched: { when: 'now', type: 'once', freq: 'daily', days: [] } },
    preview: { ic: '🔔', title: '', body: '' },
    tz: (Intl.DateTimeFormat().resolvedOptions().timeZone) || 'UTC'
  };
  window.CB = CB;

  const STEPS = ['Audience','Message','Programmation','Vérif & envoi','Résultats'];
  const DAY_NAMES = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'];
  const DEMO = { child_name: 'Awa', country: 'Sénégal', streak: '6', days_inactive: '3' };
  const SAGE_BASE = 'https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/app_assets/storyteller/';
  const SAGE_AVATARS = { bravo: SAGE_BASE+'sage_bravo.png', encouragements: SAGE_BASE+'sage_encouragements.png',
    informative: SAGE_BASE+'sage_informative.png', letsgo: SAGE_BASE+'sage_letsgo.png', thumbsup: SAGE_BASE+'sage_thumbsup.png' };
  function sageAvatar(t){
    if (!t) return SAGE_AVATARS.encouragements;
    const id = t.id||'', cat = t.category||'';
    if (id.includes('milestone') || id.includes('complete') || cat==='gamification') return SAGE_AVATARS.bravo;
    if (id.includes('at_risk') || id.includes('lost') || cat==='streak') return SAGE_AVATARS.encouragements;
    if (id.includes('miss_you') || id.includes('inactive') || id.includes('comeback') || id.includes('continue') || cat==='reengagement') return SAGE_AVATARS.letsgo;
    if (cat==='subscription') return SAGE_AVATARS.informative;
    if (cat==='engagement') return SAGE_AVATARS.thumbsup;
    return SAGE_AVATARS.encouragements;
  }

  function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function el(id){ return document.getElementById(id); }
  function val(id){ const e = el(id); return e ? e.value.trim() : ''; }
  function demoSub(t){ return String(t||'').split('{child_name}').join(DEMO.child_name).split('{country}').join(DEMO.country).split('{streak}').join(DEMO.streak).split('{days_inactive}').join(DEMO.days_inactive); }

  // ---- Stepper -------------------------------------------------------------
  function renderSteps(){
    el('cb-steps').innerHTML = STEPS.map((s,i)=>{
      const n = i+1; const cls = n===CB.step ? 'on' : (n<CB.step ? 'done' : '');
      return '<div class="cb-step '+cls+'" onclick="cbGoto('+n+')"><span class="num">'+(n<CB.step?'✓':n)+'</span><span>'+s+'</span></div>';
    }).join('');
    renderContext();
  }
  function renderContext(){
    const s = CB.sel; const parts = [];
    if (s.list) parts.push('<span><b>'+esc(s.list.name)+'</b> · '+(s.list.fcm_count||0)+' joignables push</span>');
    else parts.push('<span class="muted">Aucune audience sélectionnée</span>');
    parts.push('<span>'+(s.channel==='email'?'📧 Email':'🔔 Push')+'</span>');
    if (s.channel==='push') parts.push('<span>'+(s.mode==='custom'?'Message personnalisé':(s.template?('Template: '+esc(s.template.name)):'Aucun template'))+'</span>');
    parts.push('<span>'+(s.sched.when==='schedule'?'📅 Programmé':'📤 Immédiat')+'</span>');
    el('cb-context').innerHTML = parts.join('');
  }

  window.cbGoto = function(n){
    // L'étape 5 (suivi des campagnes) est une simple consultation : accès direct autorisé.
    if (n>CB.step && n!==5){
      if (CB.step===1 && !CB.sel.list) { alert('Choisis d\'abord un segment.'); return; }
      if (CB.step===2 && !cbMessageValid()) { alert('Complète ton message (template ou titre + corps).'); return; }
    }
    CB.step = n;
    document.querySelectorAll('.cb-panel').forEach(p => p.classList.toggle('on', +p.dataset.step===n));
    renderSteps();
    if (n===4) buildRecap();
    if (n===5) { cbResultsTab('queue'); }
    window.scrollTo({top:0, behavior:'smooth'});
  };

  // ---- Step 1 : audience ---------------------------------------------------
  async function loadLists(){
    try {
      const r = await fetch('/api/notifications-v2/lists'); const d = await r.json();
      if (d.success){ CB.lists = d.lists||[]; CB.categories = d.categories||[]; cbRenderLists(); cbApplyPrefill(); }
      else el('cb-lists').innerHTML = '<div class="cb-hint">Erreur : '+esc(d.error||'')+'</div>';
    } catch(e){ el('cb-lists').innerHTML = '<div class="cb-hint">Erreur de chargement.</div>'; }
  }
  window.cbRenderLists = function(){
    const q = (val('cb-list-search')||'').toLowerCase();
    let lists = CB.lists.filter(l => !q || (l.name||'').toLowerCase().includes(q) || (l.description||'').toLowerCase().includes(q));
    const seg = (l)=>{
      const sel = CB.sel.list && CB.sel.list.id===l.id ? ' sel' : '';
      const pill = (l.priority==='urgent'||l.priority==='high') ? '<span class="cb-pill '+l.priority+'">'+(l.priority==='urgent'?'Urgent':'Important')+'</span>' : '';
      return '<div class="cb-seg'+sel+'" onclick="cbSelectList(\''+l.id+'\')"><div class="left"><span>'+(l.icon||'')+'</span>'
        + '<span><span class="nm">'+esc(l.name)+'</span> '+pill+'<div class="desc">'+esc(l.description||'')+'</div></span></div>'
        + '<div class="right"><span class="cb-count">'+(l.fcm_count||0)+'</span> push · '+(l.total_count||0)+' total</div></div>';
    };
    let html = '';
    const sugg = lists.filter(l => l.priority==='urgent'||l.priority==='high').sort((a,b)=> (b.total_count||0)-(a.total_count||0));
    if (sugg.length){ html += '<div class="cb-group-title">⭐ Suggérées</div>' + sugg.map(seg).join(''); }
    const cats = (CB.categories.length?CB.categories:[{id:'',name:''}]);
    cats.forEach(c=>{
      const inCat = lists.filter(l => l.category===c.id);
      if (inCat.length){ html += '<div class="cb-group-title">'+(c.icon||'')+' '+esc(c.name||c.id)+'</div>' + inCat.map(seg).join(''); }
    });
    el('cb-lists').innerHTML = html || '<div class="cb-hint">Aucun segment trouvé.</div>';
  };
  window.cbSelectList = function(id){
    CB.sel.list = CB.lists.find(l => l.id===id) || null;
    el('cb-next-1').disabled = !CB.sel.list;
    cbRenderLists(); renderContext();
  };

  // ---- Step 2 : message ----------------------------------------------------
  async function loadTemplates(){
    try {
      const r = await fetch('/api/notifications-v2/templates'); const d = await r.json();
      if (d.success){ CB.templates = d.templates||[]; renderTplCats(); cbRenderTemplates('all'); }
    } catch(e){ el('cb-templates').innerHTML = '<div class="cb-hint">Erreur de chargement.</div>'; }
  }
  function renderTplCats(){
    const cats = []; const seen = {};
    CB.templates.forEach(t => { if (t.category && !seen[t.category]){ seen[t.category]=1; cats.push({id:t.category, name:t.category_name||t.category, icon:t.category_icon||''}); }});
    el('cb-tpl-cats').innerHTML = '<button class="cb-chip on" data-cat="all" onclick="cbRenderTemplates(\'all\',this)">Tous</button>'
      + cats.map(c => '<button class="cb-chip" data-cat="'+c.id+'" onclick="cbRenderTemplates(\''+c.id+'\',this)">'+(c.icon||'')+' '+esc(c.name)+'</button>').join('');
  }
  window.cbRenderTemplates = function(cat, btn){
    if (btn){ document.querySelectorAll('#cb-tpl-cats .cb-chip').forEach(b=>b.classList.remove('on')); btn.classList.add('on'); }
    const list = CB.templates.filter(t => cat==='all' || t.category===cat);
    el('cb-templates').innerHTML = list.map(t=>{
      const sel = CB.sel.template && CB.sel.template.id===t.id ? ' sel' : '';
      const ab = t.has_variants ? '<span class="ab">A/B</span>' : '';
      return '<div class="cb-tpl'+sel+'" onclick="cbSelectTemplate(\''+t.id+'\')"><div class="th"><span>'+(t.icon||'🔔')+'</span><span>'+esc(t.name)+'</span>'+ab+'</div>'
        + '<div class="tp">'+esc(t.body_default||'')+'</div></div>';
    }).join('') || '<div class="cb-hint">Aucun template.</div>';
  };
  window.cbSelectTemplate = function(id){
    CB.sel.template = CB.templates.find(t => t.id===id) || null;
    CB.sel.templateEdited = false;
    const t = CB.sel.template;
    if (t){
      el('cb-tpl-title').value = t.title_default || '';
      el('cb-tpl-body').value = t.body_default || '';
      el('cb-tpl-edit').style.display = 'block';
      el('cb-tpl-editnote').textContent = t.has_variants ? 'Ce template a des variantes A/B (actives si tu ne modifies pas le texte).' : '';
    } else {
      el('cb-tpl-edit').style.display = 'none';
    }
    cbRenderTemplates(document.querySelector('#cb-tpl-cats .cb-chip.on')?.dataset.cat || 'all');
    cbUpdatePreview(); renderContext();
  };
  window.cbTplEdited = function(){
    const t = CB.sel.template; if (!t) return;
    CB.sel.templateEdited = (el('cb-tpl-title').value !== (t.title_default||'')) || (el('cb-tpl-body').value !== (t.body_default||''));
    el('cb-tpl-editnote').textContent = CB.sel.templateEdited
      ? '✏️ Texte modifié — envoyé comme message personnalisé (A/B désactivé).'
      : (t.has_variants ? 'Ce template a des variantes A/B (actives si tu ne modifies pas le texte).' : '');
    cbUpdatePreview();
  };
  window.cbSetChannel = function(c){
    CB.sel.channel = c;
    document.querySelectorAll('#cb-channel button').forEach((b,i)=>b.classList.toggle('on', (i===0)===(c==='push')));
    el('cb-push-block').style.display = c==='push' ? 'block':'none';
    el('cb-email-block').style.display = c==='email' ? 'block':'none';
    cbUpdatePreview(); renderContext();
  };
  window.cbSetMode = function(m){
    CB.sel.mode = m;
    document.querySelectorAll('#cb-mode button').forEach((b,i)=>b.classList.toggle('on', (i===0)===(m==='template')));
    el('cb-template-block').style.display = m==='template' ? 'block':'none';
    el('cb-custom-block').style.display = m==='custom' ? 'block':'none';
    cbUpdatePreview(); renderContext();
  };
  window.cbSyncAb = function(){ CB.sel.ab = el('cb-ab').checked; };
  window.cbInsertVar = function(v, targetId){
    const ta = el(targetId || 'cb-custom-body'); if (!ta) return;
    ta.value += v; ta.focus();
    if (targetId === 'cb-tpl-body') cbTplEdited(); else cbUpdatePreview();
  };
  window.cbUpdatePreview = async function(){
    let title='Aperçu', body='Choisis un template ou écris ton message.', avatar=SAGE_AVATARS.encouragements;
    if (CB.sel.channel==='push'){
      if (CB.sel.mode==='custom'){
        title = demoSub(val('cb-custom-title')||'Titre de la notification'); body = demoSub(val('cb-custom-body')||'Ton message ici.');
        avatar = SAGE_AVATARS.informative;
      } else if (CB.sel.template){
        avatar = sageAvatar(CB.sel.template);
        if (CB.sel.templateEdited){
          title = demoSub(el('cb-tpl-title').value || CB.sel.template.title_default);
          body = demoSub(el('cb-tpl-body').value || CB.sel.template.body_default);
        } else {
          try {
            const r = await fetch('/api/notifications-v2/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({template_id:CB.sel.template.id})});
            const d = await r.json();
            if (d.success){ title=d.rendered.title; body=d.rendered.body; }
            else { title = demoSub(CB.sel.template.title_default); body = demoSub(CB.sel.template.body_default); }
          } catch(e){ title = demoSub(CB.sel.template.title_default); body = demoSub(CB.sel.template.body_default); }
        }
      }
    } else {
      title = demoSub(val('cb-email-subject')||'Sujet de l\'email'); body = 'Aperçu email dans le récapitulatif.';
      avatar = SAGE_AVATARS.informative;
    }
    CB.preview = { title, body };
    el('cb-pv-avatar').src = avatar; el('cb-pv-title').textContent = title; el('cb-pv-body').textContent = body;
  };
  function cbMessageValid(){
    if (CB.sel.channel==='push'){
      if (CB.sel.mode==='template') return !!(CB.sel.template && val('cb-tpl-title') && val('cb-tpl-body'));
      return !!(val('cb-custom-title') && val('cb-custom-body'));
    }
    return !!(val('cb-email-subject') && val('cb-email-body'));
  }

  // ---- Step 3 : programmation ---------------------------------------------
  window.cbSetWhen = function(w){
    CB.sel.sched.when = w;
    document.querySelectorAll('#cb-when button').forEach((b,i)=>b.classList.toggle('on', (i===0)===(w==='now')));
    el('cb-sched-block').style.display = w==='schedule' ? 'block':'none';
    el('cb-now-note').style.display = w==='now' ? 'block':'none';
    renderContext();
  };
  window.cbSetSchedType = function(t){
    CB.sel.sched.type = t;
    el('cb-once').classList.toggle('on', t==='once'); el('cb-recurring').classList.toggle('on', t==='recurring');
    el('cb-date-field').style.display = t==='once' ? 'block':'none';
    el('cb-freq-field').style.display = t==='recurring' ? 'block':'none';
    cbSyncFreq();
  };
  window.cbSyncFreq = function(){
    CB.sel.sched.freq = el('cb-freq').value;
    const showDays = CB.sel.sched.type==='recurring' && CB.sel.sched.freq==='weekly';
    el('cb-days-field').style.display = showDays ? 'block':'none';
  };

  // ---- Step 4 : recap + finalize ------------------------------------------
  function scheduleObj(){
    const sc = CB.sel.sched;
    if (sc.type==='once') return { type:'once', timezone:CB.tz, scheduled_at: val('cb-date')+'T'+(val('cb-time')||'09:00') };
    const days = Array.from(document.querySelectorAll('#cb-days input:checked')).map(c=>parseInt(c.value,10));
    return { type:'recurring', timezone:CB.tz, recurrence:{ freq: el('cb-freq').value, time: val('cb-time')||'09:00', days: days, timezone: CB.tz } };
  }
  function schedText(){
    const sc = CB.sel.sched;
    if (sc.when==='now') return 'Immédiat';
    if (sc.type==='once'){ const d=val('cb-date'); return d ? ('Le '+d+' à '+(val('cb-time')||'09:00')) : '(date manquante)'; }
    const days = Array.from(document.querySelectorAll('#cb-days input:checked')).map(c=>DAY_NAMES[parseInt(c.value,10)]);
    return el('cb-freq').value==='weekly' ? ('Chaque semaine ('+days.join(', ')+') à '+(val('cb-time')||'09:00')) : ('Tous les jours à '+(val('cb-time')||'09:00'));
  }
  function buildRecap(){
    const s = CB.sel;
    const count = s.channel==='push' ? (s.list?s.list.fcm_count:0) : (s.list?s.list.total_count:0);
    const rows = [
      ['Audience', esc(s.list?s.list.name:'-')+' · <b>'+count+'</b> '+(s.channel==='push'?'joignables push':'destinataires')],
      ['Canal', s.channel==='push'?'🔔 Push':'📧 Email'],
      ['Message', esc(CB.preview.title)+'<br><span style="color:#6b7280;font-size:12px;">'+esc(CB.preview.body)+'</span>'],
      ['Envoi', esc(schedText())]
    ];
    el('cb-recap').innerHTML = rows.map(r=>'<div class="row"><span class="k">'+r[0]+'</span><span class="v">'+r[1]+'</span></div>').join('');
    el('cb-final').textContent = s.sched.when==='schedule' ? ('Programmer · '+count+' utilisateurs') : ('Envoyer à '+count+' utilisateurs');
  }
  function buildPayload(){
    const s = CB.sel;
    const useTemplateId = (s.channel==='push' && s.mode==='template' && s.template && !s.templateEdited);
    const p = { channel: s.channel, target:{ type:'list', list_id: s.list.id },
                options:{ fcm_only: s.fcmOnly, ab_test: !!(s.ab && useTemplateId) } };
    if (s.channel==='push'){
      if (s.mode==='custom') p.custom_message = { title: val('cb-custom-title'), body: val('cb-custom-body') };
      else if (useTemplateId) p.template_id = s.template.id;
      else p.custom_message = { title: val('cb-tpl-title'), body: val('cb-tpl-body') };
    } else { p.email = { subject: val('cb-email-subject'), body: val('cb-email-body') }; }
    return p;
  }
  window.cbFinalize = async function(){
    const s = CB.sel;
    if (!s.list){ alert('Audience manquante.'); return; }
    if (!cbMessageValid()){ alert('Message incomplet.'); cbGoto(2); return; }
    const scheduling = s.sched.when==='schedule';
    if (scheduling && s.channel==='email'){ alert('La programmation est disponible uniquement pour le push.'); return; }
    if (scheduling && s.sched.type==='once' && !val('cb-date')){ alert('Choisis une date.'); cbGoto(3); return; }

    const count = s.channel==='push' ? s.list.fcm_count : s.list.total_count;
    const verb = scheduling ? 'programmer' : 'envoyer';
    if (!confirm('Confirme : '+verb+' cette notification à '+count+' utilisateurs ?')) return;

    const btn = el('cb-final'); btn.disabled = true; btn.textContent = 'En cours...';
    try {
      let url, body;
      if (scheduling){ url='/api/notifications-v2/schedule'; body = Object.assign(buildPayload(), { schedule: scheduleObj(), title: CB.preview.title }); }
      else { url='/api/notifications-v2/send'; body = buildPayload(); }
      const r = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const d = await r.json();
      if (d.success){
        if (scheduling){ const w=d.next_run_at?new Date(d.next_run_at).toLocaleString('fr-FR'):''; alert('✅ Campagne mise en file. Prochain envoi : '+w); }
        else { alert('✅ Envoyé : '+(d.sent||0)+'/'+(d.total||0)); }
        cbGoto(5);
      } else { alert('Erreur : '+(d.error||'échec')); }
    } catch(e){ alert('Erreur lors de l\'envoi.'); }
    finally { btn.disabled = false; buildRecap(); }
  };

  // ---- Step 5 : résultats --------------------------------------------------
  window.cbResultsTab = function(t){
    el('cb-tab-queue').classList.toggle('on', t==='queue'); el('cb-tab-hist').classList.toggle('on', t==='hist');
    el('cb-queue').style.display = t==='queue'?'block':'none'; el('cb-hist').style.display = t==='hist'?'block':'none';
    if (t==='queue') loadQueue(); else loadHistory();
  };
  function schedDesc(c){
    const s=c.schedule||{};
    if (s.type==='recurring'){ const rec=s.recurrence||{}; if (rec.freq==='weekly'){ const ds=(rec.days||[]).map(d=>DAY_NAMES[d]).join(', '); return 'Chaque semaine ('+ds+') à '+(rec.time||''); } return 'Tous les jours à '+(rec.time||''); }
    return 'Une fois';
  }
  async function loadQueue(){
    const c = el('cb-queue'); c.innerHTML = '<div class="cb-hint">Chargement...</div>';
    try {
      const r = await fetch('/api/notifications-v2/scheduled'); const d = await r.json();
      const items = (d&&d.campaigns)||[];
      CB.queue = {};
      if (!items.length){ c.innerHTML = '<div class="cb-hint">Aucune campagne en file.</div>'; return; }
      c.innerHTML = '<p class="cb-hint">Clique sur une campagne pour la modifier.</p>' + items.map(x=>{
        CB.queue[x.id] = x;
        const next = x.next_run_at ? new Date(x.next_run_at).toLocaleString('fr-FR') : '-';
        const act = (x.status==='queued'||x.status==='sending');
        return '<div class="cb-seg" style="display:block; cursor:'+(act?'pointer':'default')+';"'+(act?' onclick="cbEditOpen(\''+x.id+'\')"':'')+'>'
          +'<div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">'
          +'<div class="left"><span>'+(x.channel==='email'?'📧':'🔔')+'</span>'
          +'<span><span class="nm">'+esc(x.title||'(sans titre)')+'</span><div class="desc">⏰ '+next+' · 🔁 '+schedDesc(x)+'</div></span></div>'
          +'<div class="right" onclick="event.stopPropagation();"><span class="cb-status '+x.status+'">'+x.status+'</span>'
          +(act?' <button class="cb-btn" style="padding:4px 10px;font-size:12px;" onclick="cbEditOpen(\''+x.id+'\')">✏️ Éditer</button>'
              +' <button class="cb-btn" style="padding:4px 10px;font-size:12px;" onclick="cbSendNow(\''+x.id+'\')">▶️ Envoyer</button>'
              +' <button class="cb-btn" style="padding:4px 10px;font-size:12px;border-color:#fca5a5;color:#b91c1c;" onclick="cbDelete(\''+x.id+'\')">🗑️ Supprimer</button>':'')
          +'</div></div>'
          +'<div id="cb-edit-'+x.id+'" style="display:none; margin-top:12px; border-top:1px solid #eef0f2; padding-top:12px;" onclick="event.stopPropagation();"></div>'
          +'</div>';
      }).join('');
    } catch(e){ c.innerHTML = '<div class="cb-hint">Erreur.</div>'; }
  }
  async function loadHistory(){
    const c = el('cb-hist'); c.innerHTML = '<div class="cb-hint">Chargement...</div>';
    try {
      const r = await fetch('/api/notifications-v2/history?limit=50'); const d = await r.json();
      const items = (d&&d.history)||[];
      if (!items.length){ c.innerHTML = '<div class="cb-hint">Aucun envoi enregistré.</div>'; return; }
      const rows = items.map(h=>{
        const when = h.sent_at ? new Date(h.sent_at).toLocaleString('fr-FR') : '-';
        const taps = (h.open_count && h.open_count>0) ? String(h.open_count) : '<span class="cb-pending">à venir</span>';
        return '<tr><td>'+when+'</td><td>'+(h.channel==='email'?'📧':'🔔')+' '+esc(h.title||h.type||'')+'</td><td>'+(h.total_targeted||0)+'</td><td>'+(h.total_sent||0)+'</td><td>'+(h.total_failed||0)+'</td><td>'+taps+'</td></tr>';
      }).join('');
      c.innerHTML = '<table class="cb-htable"><thead><tr><th>Date</th><th>Notification</th><th>Ciblés</th><th>Envoyés</th><th>Échecs</th><th>Touches</th></tr></thead><tbody>'+rows+'</tbody></table>';
    } catch(e){ c.innerHTML = '<div class="cb-hint">Erreur.</div>'; }
  }
  window.cbDelete = async function(id){
    if (!confirm('Supprimer définitivement cette campagne ?')) return;
    try { const r = await fetch('/api/notifications-v2/scheduled/'+id+'/delete',{method:'POST'}); const d=await r.json(); if(d.success) loadQueue(); else alert('Erreur : '+(d.error||'')); } catch(e){ alert('Erreur'); }
  };

  // ---- Édition inline d'une campagne en file -------------------------------
  window.cbEditOpen = function(id){
    const box = el('cb-edit-'+id); if (!box) return;
    if (box.style.display==='block'){ box.style.display='none'; box.innerHTML=''; return; }
    document.querySelectorAll('[id^="cb-edit-"]').forEach(b=>{ b.style.display='none'; b.innerHTML=''; });
    const x = CB.queue[id]; if (!x) return;
    const p = x.payload||{}, cm = p.custom_message||{}, s = x.schedule||{}, rec = s.recurrence||{};
    const isRec = s.type==='recurring';
    const time = (isRec ? (rec.time||'') : ((s.scheduled_at||'').slice(11,16))) || '09:00';
    const date = (s.scheduled_at||'').slice(0,10);
    const freq = rec.freq || 'daily';
    const days = rec.days || [];
    box.style.display = 'block';
    box.innerHTML =
      '<div class="cb-field"><label>Titre</label><input id="ce-title-'+id+'" value="'+esc(x.title||'')+'"></div>'
      +'<div class="cb-field"><label>Message — titre</label><input id="ce-mtitle-'+id+'" value="'+esc(cm.title||'')+'"></div>'
      +'<div class="cb-field"><label>Message — corps</label><textarea id="ce-mbody-'+id+'">'+esc(cm.body||'')+'</textarea></div>'
      +'<div class="cb-seg-row">'
        +'<button type="button" class="cb-chip '+(!isRec?'on':'')+'" id="ce-once-'+id+'" onclick="cbEditSetType(\''+id+'\',\'once\')">Une seule fois</button>'
        +'<button type="button" class="cb-chip '+(isRec?'on':'')+'" id="ce-rec-'+id+'" onclick="cbEditSetType(\''+id+'\',\'recurring\')">Récurrent</button>'
      +'</div>'
      +'<div style="display:flex; gap:12px; flex-wrap:wrap; align-items:flex-end;">'
        +'<div class="cb-field" id="ce-date-field-'+id+'" style="max-width:200px; display:'+(isRec?'none':'block')+';"><label>Date</label><input type="date" id="ce-date-'+id+'" value="'+esc(date)+'"></div>'
        +'<div class="cb-field" style="max-width:160px;"><label>Heure</label><input type="time" id="ce-time-'+id+'" value="'+esc(time)+'"></div>'
        +'<div class="cb-field" id="ce-freq-field-'+id+'" style="max-width:200px; display:'+(isRec?'block':'none')+';"><label>Fréquence</label>'
          +'<select id="ce-freq-'+id+'" onchange="cbEditSyncFreq(\''+id+'\')"><option value="daily"'+(freq==='daily'?' selected':'')+'>Tous les jours</option><option value="weekly"'+(freq==='weekly'?' selected':'')+'>Chaque semaine</option></select></div>'
      +'</div>'
      +'<div class="cb-field" id="ce-days-field-'+id+'" style="display:'+((isRec&&freq==='weekly')?'block':'none')+';"><label>Jours</label><div class="cb-days" id="ce-days-'+id+'">'
        + DAY_NAMES.map((dn,i)=>'<label><input type="checkbox" value="'+i+'"'+(days.indexOf(i)>=0?' checked':'')+'>'+dn+'</label>').join('')
      +'</div></div>'
      +'<div class="cb-nav" style="margin-top:8px;">'
        +'<button class="cb-btn" onclick="cbEditOpen(\''+id+'\')">Fermer</button>'
        +'<button class="cb-btn primary" onclick="cbEditSave(\''+id+'\')">💾 Enregistrer</button>'
      +'</div>';
  };
  window.cbEditSetType = function(id, t){
    el('ce-once-'+id).classList.toggle('on', t==='once');
    el('ce-rec-'+id).classList.toggle('on', t==='recurring');
    el('ce-date-field-'+id).style.display = t==='once'?'block':'none';
    el('ce-freq-field-'+id).style.display = t==='recurring'?'block':'none';
    cbEditSyncFreq(id);
  };
  window.cbEditSyncFreq = function(id){
    const isRec = el('ce-rec-'+id).classList.contains('on');
    el('ce-days-field-'+id).style.display = (isRec && el('ce-freq-'+id).value==='weekly')?'block':'none';
  };
  window.cbEditSave = async function(id){
    const x = CB.queue[id]; if (!x) return;
    const title = (el('ce-title-'+id).value||'').trim();
    const mtitle = (el('ce-mtitle-'+id).value||'').trim();
    const mbody = (el('ce-mbody-'+id).value||'').trim();
    if (!mtitle || !mbody){ alert('Le titre et le corps du message sont requis.'); return; }
    const isRec = el('ce-rec-'+id).classList.contains('on');
    const time = el('ce-time-'+id).value || '09:00';
    const tz = (x.schedule&&x.schedule.timezone) || CB.tz;
    let schedule;
    if (isRec){
      const freq = el('ce-freq-'+id).value;
      const days = Array.from(document.querySelectorAll('#ce-days-'+id+' input:checked')).map(c=>parseInt(c.value,10));
      if (freq==='weekly' && !days.length){ alert('Choisis au moins un jour.'); return; }
      schedule = { type:'recurring', timezone:tz, recurrence:{ freq:freq, time:time, days:days, timezone:tz } };
    } else {
      const date = el('ce-date-'+id).value;
      if (!date){ alert('Choisis une date.'); return; }
      schedule = { type:'once', timezone:tz, scheduled_at: date+'T'+time };
    }
    const p = Object.assign({}, x.payload||{});
    p.custom_message = { title: mtitle, body: mbody };
    delete p.template_id;
    const body = Object.assign({}, p, { title: title||mtitle, schedule: schedule });
    try {
      const r = await fetch('/api/notifications-v2/scheduled/'+id+'/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const d = await r.json();
      if (d.success){ loadQueue(); } else { alert('Erreur : '+(d.error||'échec')); }
    } catch(e){ alert('Erreur lors de la mise à jour.'); }
  };
  window.cbSendNow = async function(id){
    if (!confirm('Envoyer cette campagne maintenant ?')) return;
    try { const r = await fetch('/api/notifications-v2/scheduled/'+id+'/send-now',{method:'POST'}); const d=await r.json(); if(d.success) alert('✅ Envoyé : '+(d.sent||0)+'/'+(d.total||0)); else alert('Erreur : '+(d.error||'')); loadQueue(); } catch(e){ alert('Erreur'); }
  };

  window.cbReset = function(){
    CB.sel.list=null; CB.sel.template=null; CB.sel.templateEdited=false; CB.sel.mode='template'; CB.sel.channel='push'; CB.sel.ab=false; CB.sel.sched={when:'now',type:'once',freq:'daily',days:[]};
    ['cb-custom-title','cb-custom-body','cb-email-subject','cb-email-body','cb-list-search','cb-tpl-title','cb-tpl-body'].forEach(i=>{ if(el(i)) el(i).value=''; });
    if (el('cb-ab')) el('cb-ab').checked=false;
    if (el('cb-tpl-edit')) el('cb-tpl-edit').style.display='none';
    el('cb-next-1').disabled = true;
    cbSetChannel('push'); cbSetMode('template'); cbSetWhen('now'); cbUpdatePreview(); cbRenderLists();
    cbGoto(1);
  };

  // ---- Prefill depuis le Rapport GA4 (?segment=&title=&body=&source=analytics) ----
  let cbPrefillDone = false;
  window.cbApplyPrefill = function(){
    if (cbPrefillDone) return;
    try {
      const p = new URLSearchParams(window.location.search);
      const seg = p.get('segment'), title = p.get('title'), body = p.get('body');
      if (!seg && !title && !body) return;
      cbPrefillDone = true;
      if (seg && CB.lists.find(l => l.id===seg)) cbSelectList(seg);
      if (title || body){
        cbSetChannel('push'); cbSetMode('custom');
        if (title && el('cb-custom-title')) el('cb-custom-title').value = title;
        if (body && el('cb-custom-body')) el('cb-custom-body').value = body;
        cbUpdatePreview();
      }
      if (p.get('source')==='analytics' && !el('cb-analytics-banner')){
        const host = document.querySelector('.container') || document.body;
        if (host){
          const d = document.createElement('div');
          d.id = 'cb-analytics-banner';
          d.style.cssText = 'margin:12px 0;padding:12px 16px;border-radius:8px;background:#e8f0fe;border:1px solid #1a73e8;color:#174ea6;';
          d.innerHTML = '📉 Campagne pré-remplie depuis le <b>Rapport GA4</b> — segment et message suggérés. Vérifie les destinataires, puis avance dans les étapes pour envoyer.';
          host.insertBefore(d, host.firstChild);
        }
      }
      renderContext();
    } catch(e){ console.error('cbApplyPrefill', e); }
  };

  // ---- init ----------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function(){
    renderSteps();
    // jours de la semaine
    el('cb-days').innerHTML = DAY_NAMES.map((d,i)=>'<label><input type="checkbox" value="'+i+'">'+d+'</label>').join('');
    el('cb-tz-note').textContent = 'Fuseau horaire : '+CB.tz+' (heure locale du destinataire pour le récurrent).';
    loadLists(); loadTemplates(); cbUpdatePreview();
  });
})();
</script>
'''
