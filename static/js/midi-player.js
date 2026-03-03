/**
 * Harmonia — World Music MIDI Player
 * Uses Tone.js + @tonejs/midi for web-based MIDI playback
 * Loads catalog.json for multi-region support
 *
 * @version 2.0 (refactored)
 */
;(function () {
  'use strict';

  // ─── State ──────────────────────────────────────────────
  let catalog = null;
  let currentRegion = null;
  let synths = [];
  let currentMidi = null;
  let isPlaying = false;
  let startTime = 0;
  let progressInterval = null;
  let allTracks = [];
  let currentTrackIndex = -1;
  let volumeDb = -8;

  // ─── DOM Helpers ────────────────────────────────────────
  /** @param {string} id @returns {HTMLElement|null} */
  function $(id) { return document.getElementById(id); }

  /** Safe textContent setter */
  function setText(id, text) {
    const el = $(id);
    if (el) el.textContent = text;
  }

  /** Safe style setter */
  function setDisplay(id, value) {
    const el = $(id);
    if (el) el.style.display = value;
  }

  /** Safe width setter (for progress bars) */
  function setWidth(id, pct) {
    const el = $(id);
    if (el) el.style.width = pct + '%';
  }

  // ─── Catalog ────────────────────────────────────────────
  async function loadCatalog() {
    try {
      const resp = await fetch('/catalog.json');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      catalog = await resp.json();
      setText('hero-total', (catalog.totalSongs || 0).toLocaleString());
      buildRegionGrid();
    } catch (e) {
      console.error('Failed to load catalog:', e);
    }
  }

  // ─── Region Grid (Home) ─────────────────────────────────
  function buildRegionGrid() {
    const grid = $('region-grid');
    if (!grid || !catalog) return;
    grid.innerHTML = '';
    for (const region of catalog.regions) {
      const card = document.createElement('div');
      card.className = 'region-card fade-in';
      card.onclick = () => showRegion(region.id);
      card.innerHTML = `
        <span class="rc-emoji">${esc(region.emoji)}</span>
        <div class="rc-name">${esc(region.name)}</div>
        <div class="rc-count">${region.songCount || region.songs?.length || 0}곡</div>
        <div class="rc-desc">${esc((region.description || '').substring(0, 100))}...</div>
      `;
      grid.appendChild(card);
    }
    observeFadeIns();
  }

  /** Minimal HTML escape */
  function esc(s) {
    if (!s) return '';
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ─── Navigation ─────────────────────────────────────────
  function showHome() {
    setDisplay('home-view', '');
    setDisplay('region-view', 'none');
    setDisplay('timeline-view', 'none');
    window.scrollTo(0, 0);
  }

  function showRegion(regionId) {
    if (!catalog) return;
    const region = catalog.regions.find(r => r.id === regionId);
    if (!region) return;
    currentRegion = region;

    setDisplay('home-view', 'none');
    setDisplay('region-view', '');
    setDisplay('timeline-view', 'none');

    setText('region-emoji', region.emoji);
    setText('region-name', region.name);
    setText('region-song-count', `${region.songCount || 0}곡`);
    setText('region-description', region.description || '');

    // Korean-specific content
    const koreanContent = $('korean-content');
    if (koreanContent) koreanContent.style.display = regionId === 'korean' ? '' : 'none';

    setText('player-title', `🎧 ${region.emoji} ${region.name} MIDI 플레이어`);
    setText('player-subtitle', `${region.songCount || 0}곡 — 곡을 클릭하면 브라우저에서 바로 재생됩니다`);

    buildPlayerUI(region);
    window.scrollTo(0, 0);
    observeFadeIns();
  }

  // ─── Player UI ──────────────────────────────────────────
  function buildPlayerUI(region) {
    const container = $('midi-player-app');
    if (!container) return;

    allTracks = [];
    const parts = [
      `<div class="mp-controls">
        <div class="mp-now-playing">
          <div class="mp-title" id="mp-title">곡을 선택하세요</div>
          <div class="mp-sub" id="mp-sub"></div>
        </div>
        <div class="mp-buttons">
          <button id="mp-prev" class="mp-btn" onclick="Harmonia.prevTrack()">⏮</button>
          <button id="mp-play" class="mp-btn" disabled onclick="Harmonia.togglePlay()">▶ 재생</button>
          <button id="mp-stop" class="mp-btn" onclick="Harmonia.stop()">⏹</button>
          <button id="mp-next" class="mp-btn" onclick="Harmonia.nextTrack()">⏭</button>
          <div class="mp-progress-wrap" onclick="Harmonia.seekInPlayer(event)">
            <div class="mp-progress" id="mp-progress"></div>
          </div>
          <span class="mp-time" id="mp-time">0:00</span>
        </div>
      </div>
      <div class="mp-search">
        <input type="text" placeholder="이 지역에서 검색..." oninput="Harmonia.filterTracks(this.value)">
      </div>
      <div class="mp-catalog">`
    ];

    let trackIdx = 0;
    for (const group of (region.groups || [])) {
      parts.push(`<div class="mp-suite">
        <div class="mp-suite-header" onclick="Harmonia.toggleSuite(this)">
          <span class="mp-arrow">▶</span> ${esc(group.name)}
          ${group.era ? `<span class="mp-era">${esc(group.era)}</span>` : ''}
          <span class="mp-track-count">${(group.tracks || []).length}곡</span>
        </div>
        <div class="mp-suite-list" style="display:none">
          ${group.history ? `<div class="mp-history">${esc(group.history)}</div>` : ''}`);

      for (const track of (group.tracks || [])) {
        const encodedFile = encodeURIComponent(track.file);
        const basePath = region.basePath || '/static/midi/';
        allTracks.push({
          file: track.file,
          title: track.title,
          group: group.name,
          basePath,
          info: track.info || '',
          index: trackIdx
        });
        const infoHtml = track.info ? `<div class="mp-track-info">${esc(track.info)}</div>` : '';
        parts.push(`<div class="mp-track" data-idx="${trackIdx}" data-title="${esc(track.title.toLowerCase())}" onclick="Harmonia.loadTrack(${trackIdx})">
          <span class="mp-track-icon">♪</span> ${esc(track.title)}
          ${infoHtml}
          <a href="${basePath}${encodedFile}" download class="mp-dl" title="다운로드" onclick="event.stopPropagation()">⬇</a>
        </div>`);
        trackIdx++;
      }
      parts.push(`</div></div>`);
    }
    parts.push(`</div>`);
    container.innerHTML = parts.join('');
  }

  function toggleSuite(el) {
    const list = el.nextElementSibling;
    const arrow = el.querySelector('.mp-arrow');
    if (!list || !arrow) return;
    const hidden = list.style.display === 'none';
    list.style.display = hidden ? 'block' : 'none';
    arrow.textContent = hidden ? '▼' : '▶';
  }

  function filterTracks(query) {
    query = (query || '').toLowerCase().trim();
    document.querySelectorAll('.mp-track').forEach(el => {
      const title = el.getAttribute('data-title') || '';
      el.classList.toggle('hidden', !!(query && !title.includes(query)));
    });
  }

  // ─── Track Loading ──────────────────────────────────────
  async function loadTrackByIndex(idx) {
    if (idx < 0 || idx >= allTracks.length) return;
    currentTrackIndex = idx;
    const track = allTracks[idx];

    // Highlight active track
    document.querySelectorAll('.mp-track.active').forEach(t => t.classList.remove('active'));
    const el = document.querySelector(`.mp-track[data-idx="${idx}"]`);
    if (el) {
      el.classList.add('active');
      // Expand parent suite if collapsed
      const suiteList = el.closest('.mp-suite-list');
      if (suiteList && suiteList.style.display === 'none') {
        suiteList.style.display = 'block';
        const arrow = suiteList.previousElementSibling?.querySelector('.mp-arrow');
        if (arrow) arrow.textContent = '▼';
      }
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }

    stopMidi();

    setText('mp-title', track.title);
    setText('mp-sub', track.info ? `${track.group} — ${track.info}` : track.group);
    const playBtn = $('mp-play');
    if (playBtn) playBtn.disabled = true;
    setText('mp-time', '로딩...');

    showBottomPlayer(track.title, currentRegion ? currentRegion.name : '');

    try {
      const url = `${track.basePath}${encodeURIComponent(track.file)}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const arrayBuffer = await response.arrayBuffer();
      currentMidi = new Midi(arrayBuffer);
      if (playBtn) playBtn.disabled = false;
      setText('mp-time', formatTime(0) + ' / ' + formatTime(currentMidi.duration));
      updateBottomTime(0, currentMidi.duration);
      playMidi();
    } catch (e) {
      setText('mp-time', '로딩 실패');
      console.error('Track load error:', e);
    }
  }

  // ─── Playback (shared core) ─────────────────────────────
  /**
   * Core play function. Schedules all MIDI notes from a given offset.
   * @param {number} [offset=0] Start position in seconds
   */
  async function startPlayback(offset) {
    if (!currentMidi) return;
    offset = offset || 0;

    if (Tone.context.state !== 'running') {
      await Tone.start();
    }

    disposeSynths();

    const now = Tone.now() + 0.1;
    startTime = now - offset;

    currentMidi.tracks.forEach(track => {
      const synth = new Tone.PolySynth(Tone.Synth, {
        envelope: { attack: 0.02, decay: 0.1, sustain: 0.3, release: 0.8 },
        oscillator: { type: 'triangle8' }
      }).toDestination();
      synth.volume.value = volumeDb;
      synths.push(synth);

      track.notes.forEach(note => {
        if (note.time >= offset) {
          try {
            synth.triggerAttackRelease(
              note.name, note.duration,
              note.time - offset + now, note.velocity
            );
          } catch (e) {
            // Skip invalid notes silently
          }
        }
      });
    });

    isPlaying = true;
    updatePlayButton(true);
    Tone.Transport.start();

    const totalDur = currentMidi.duration;
    clearInterval(progressInterval);
    progressInterval = setInterval(() => {
      const elapsed = Tone.now() - startTime;
      const pct = Math.min(elapsed / totalDur * 100, 100);

      setWidth('mp-progress', pct);
      setText('mp-time', formatTime(elapsed) + ' / ' + formatTime(totalDur));
      updateBottomProgress(pct);
      updateBottomTime(elapsed, totalDur);

      if (elapsed >= totalDur) {
        stopMidi();
        playNextTrack();
      }
    }, 200);
  }

  function playMidi() { return startPlayback(0); }

  function pauseMidi() {
    disposeSynths();
    isPlaying = false;
    clearInterval(progressInterval);
    updatePlayButton(false);
  }

  function stopMidi() {
    disposeSynths();
    isPlaying = false;
    clearInterval(progressInterval);
    updatePlayButton(false);

    setWidth('mp-progress', 0);
    if (currentMidi) {
      setText('mp-time', '0:00 / ' + formatTime(currentMidi.duration));
    }
    const playBtn = $('mp-play');
    if (playBtn) playBtn.disabled = !currentMidi;

    updateBottomProgress(0);
    if (currentMidi) updateBottomTime(0, currentMidi.duration);
  }

  function disposeSynths() {
    synths.forEach(s => { try { s.dispose(); } catch (_) {} });
    synths = [];
  }

  function togglePlay() {
    if (!currentMidi) return;
    isPlaying ? pauseMidi() : playMidi();
  }

  function playNextTrack() {
    if (allTracks.length === 0) return;
    loadTrackByIndex((currentTrackIndex + 1) % allTracks.length);
  }

  function playPrevTrack() {
    if (allTracks.length === 0) return;
    loadTrackByIndex(currentTrackIndex <= 0 ? allTracks.length - 1 : currentTrackIndex - 1);
  }

  function setVolume(val) {
    volumeDb = (val / 100) * 24 - 24;
    synths.forEach(s => { try { s.volume.value = volumeDb; } catch (_) {} });
  }

  function seekInPlayer(e) {
    if (!currentMidi) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const seekTime = pct * currentMidi.duration;
    stopMidi();
    startPlayback(seekTime);
  }

  // ─── UI Updates ─────────────────────────────────────────
  function updatePlayButton(playing) {
    setText('mp-play', playing ? '⏸ 일시정지' : '▶ 재생');
    setText('bp-play', playing ? '⏸' : '▶');
  }

  function showBottomPlayer(title, regionName) {
    const bar = $('bottom-player');
    if (bar) bar.style.display = 'flex';
    document.body.classList.add('player-active');
    setText('bp-title', title);
    setText('bp-region', regionName);
  }

  function updateBottomProgress(pct) { setWidth('bp-progress', pct); }
  function updateBottomTime(elapsed, _total) { setText('bp-time', formatTime(elapsed)); }

  function formatTime(seconds) {
    if (!seconds || seconds < 0) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return m + ':' + (s < 10 ? '0' : '') + s;
  }

  // ─── Global Search (210k DB version) ──────────────────
  async function handleGlobalSearch(query) {
    const resultsEl = $('global-search-results');
    if (!query || query.trim().length < 2) {
      if (resultsEl) resultsEl.style.display = 'none';
      return;
    }

    const loader = $('search-loading');
    if (loader) loader.style.display = 'block';

    try {
      const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const results = await resp.json();
      
      if (loader) loader.style.display = 'none';
      
      if (!results || results.length === 0) {
        resultsEl.style.display = 'none';
        return;
      }

      resultsEl.style.display = '';
      resultsEl.innerHTML = results.map(r => `
        <div class="search-result-item" onclick="Harmonia.playById(${r.id}, '${esc(r.title)}')">
          <span class="sr-emoji">🎵</span>
          <div class="sr-info">
            <span class="sr-title">${esc(r.title)}</span>
            <span class="sr-meta">${esc(r.composer || '작자 미상')} | ${esc(r.dataset)}</span>
          </div>
        </div>
      `).join('');
    } catch (e) {
      if (loader) loader.style.display = 'none';
      console.error('Search failed:', e);
    }
  }

  /** Show songs from a specific curation channel */
  async function showChannel(channelId, channelName) {
    stopMidi();
    
    // UI 준비
    setDisplay('home-view', 'none');
    setDisplay('region-view', '');
    setDisplay('timeline-view', 'none');

    setText('region-emoji', '📺');
    setText('region-name', channelName);
    setText('region-description', `${channelName} 채널의 추천 플레이리스트입니다.`);
    setText('player-title', `🎧 ${channelName} 플레이리스트`);
    
    const container = $('midi-player-app');
    if (container) container.innerHTML = '<div class="loading-p">채널 데이터를 불러오는 중...</div>';

    try {
      const resp = await fetch(`/api/channel?id=${channelId}`);
      const songs = await resp.json();
      
      allTracks = [];
      let html = `<div class="mp-catalog">`;
      
      songs.forEach((track, idx) => {
        allTracks.push({
          id: track.id,
          title: track.title,
          composer: track.composer,
          dataset: track.dataset,
          index: idx,
          isStreaming: true
        });
        
        html += `
          <div class="mp-track" data-idx="${idx}" onclick="Harmonia.loadStreamingTrack(${idx})">
            <span class="mp-track-icon">▶</span>
            <div class="mp-track-body">
              <div class="mp-track-title">${esc(track.title)}</div>
              <div class="mp-track-info">${esc(track.composer || '작자 미상')} | ${esc(track.dataset)}</div>
            </div>
          </div>`;
      });
      
      html += `</div>`;
      if (container) container.innerHTML = html;
      window.scrollTo(0, 0);
    } catch (e) {
      console.error('Channel load error:', e);
    }
  }

  async function loadStreamingTrack(idx) {
    const track = allTracks[idx];
    if (!track) return;

    document.querySelectorAll('.mp-track.active').forEach(t => t.classList.remove('active'));
    const el = document.querySelector(`.mp-track[data-idx="${idx}"]`);
    if (el) el.classList.add('active');

    playById(track.id, track.title);
  }

  function searchResultClick(regionId, encodedTitle) {
    const title = decodeURIComponent(encodedTitle);
    const resultsEl = $('global-search-results');
    const searchEl = $('global-search');
    if (resultsEl) resultsEl.style.display = 'none';
    if (searchEl) searchEl.value = '';

    showRegion(regionId);
    const idx = allTracks.findIndex(t => t.title === title);
    if (idx >= 0) {
      setTimeout(() => loadTrackByIndex(idx), 100);
    }
  }

  // Close search on outside click
  document.addEventListener('click', (e) => {
    const searchArea = document.querySelector('.hero-search');
    const results = $('global-search-results');
    if (searchArea && results && !searchArea.contains(e.target)) {
      results.style.display = 'none';
    }
  });

  // ─── Timeline ───────────────────────────────────────────
  function showTimeline() {
    setDisplay('home-view', 'none');
    setDisplay('region-view', 'none');
    setDisplay('timeline-view', '');
    buildTimeline();
    window.scrollTo(0, 0);
  }

  function buildTimeline() {
    const container = $('timeline-content');
    if (!container || !catalog || !catalog.timeline) return;

    const events = [...catalog.timeline].sort((a, b) => a.year - b.year);
    const parts = [];

    for (const ev of events) {
      const yearStr = ev.year < 0 ? `BC ${Math.abs(ev.year)}` : `${ev.year}`;
      const sideClass = ev.side === 'korea' ? 'tl-left' : 'tl-right';
      const highlight = (ev.title || '').includes('★') ? ' tl-highlight' : '';

      let playBtn = '';
      if (ev.trackTitle && ev.regionId) {
        // Use data attributes for robust matching
        const safeTitle = esc(ev.trackTitle);
        const safeRegion = esc(ev.regionId);
        playBtn = `<button class="tl-play-btn" data-region="${safeRegion}" data-track="${safeTitle}" onclick="Harmonia.timelinePlay(this)">▶ 듣기</button>`;
      }

      parts.push(`
        <div class="tl-item ${sideClass}${highlight}">
          <div class="tl-year">${yearStr}</div>
          <div class="tl-card">
            <div class="tl-side-label">${ev.side === 'korea' ? '🇰🇷 한국' : '🌍 세계'}</div>
            <h3 class="tl-title">${esc(ev.title)}</h3>
            <p class="tl-desc">${esc(ev.desc)}</p>
            ${playBtn}
          </div>
        </div>
      `);
    }

    container.innerHTML = parts.join('');
    observeFadeIns();
  }

  /**
   * Play a track from the timeline. Uses data attributes for robust matching.
   * @param {HTMLElement} btn Button element with data-region and data-track
   */
  async function timelinePlay(btn) {
    if (!catalog || !btn) return;
    const regionId = btn.getAttribute('data-region');
    const trackTitle = btn.getAttribute('data-track');
    if (!regionId || !trackTitle) return;

    const region = catalog.regions.find(r => r.id === regionId);
    if (!region) return;

    // Find track by title (try exact, then partial)
    let targetFile = null;
    const basePath = region.basePath || '/static/midi/';
    for (const group of (region.groups || [])) {
      for (const track of (group.tracks || [])) {
        if (track.title === trackTitle || track.file.includes(trackTitle)) {
          targetFile = track.file;
          break;
        }
      }
      if (targetFile) break;
    }
    if (!targetFile) {
      console.warn(`Timeline: track not found: ${trackTitle} in ${regionId}`);
      return;
    }

    try {
      if (Tone.context.state !== 'running') await Tone.start();
      stopMidi();
      showBottomPlayer(trackTitle, region.name);

      const url = `${basePath}${encodeURIComponent(targetFile)}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const arrayBuffer = await response.arrayBuffer();
      currentMidi = new Midi(arrayBuffer);
      updateBottomTime(0, currentMidi.duration);
      await startPlayback(0);
    } catch (e) {
      console.error('Timeline play error:', e);
    }
  }

  // ─── Init ───────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', loadCatalog);

  // ─── Mobile Menu ─────────────────────────────────────────
  function toggleMobileMenu() {
    const menu = $('mobile-menu');
    if (menu) menu.classList.toggle('open');
  }
  function closeMobileMenu() {
    const menu = $('mobile-menu');
    if (menu) menu.classList.remove('open');
  }

  // ─── Scroll Fade-In ─────────────────────────────────────
  const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
  }, { threshold: 0.1 });

  function observeFadeIns() {
    document.querySelectorAll('.fade-in:not(.visible)').forEach(el => fadeObserver.observe(el));
  }

  // Run initial observation
  document.addEventListener('DOMContentLoaded', observeFadeIns);

  // ─── Public API (for onclick handlers in HTML) ──────────
  window.Harmonia = {
    showHome,
    showRegion,
    showTimeline,
    togglePlay,
    stop: stopMidi,
    nextTrack: playNextTrack,
    prevTrack: playPrevTrack,
    loadTrack: loadTrackByIndex,
    setVolume,
    seekInPlayer,
    seekTo: seekInPlayer,
    filterTracks,
    toggleSuite,
    handleGlobalSearch,
    searchClick: searchResultClick,
    playById,
    showChannel,
    loadStreamingTrack,
    timelinePlay,
    toggleMobile: toggleMobileMenu,
    closeMobile: closeMobileMenu,
  };
})();
