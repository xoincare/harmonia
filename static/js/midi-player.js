/**
 * Harmonia — World Music MIDI Player
 * Uses Tone.js + @tonejs/midi for web-based MIDI playback
 * Loads catalog.json for multi-region support
 */

let catalog = null;
let currentRegion = null;
let synths = [];
let currentMidi = null;
let isPlaying = false;
let startTime = 0;
let progressInterval = null;
let currentTrackEl = null;
let allTracks = []; // flat list for next/prev
let currentTrackIndex = -1;
let volumeDb = -8;

// === Catalog Loading ===
async function loadCatalog() {
  const resp = await fetch('/catalog.json');
  catalog = await resp.json();
  document.getElementById('hero-total').textContent = catalog.totalSongs.toLocaleString();
  buildRegionGrid();
}

// === Region Grid (Home) ===
function buildRegionGrid() {
  const grid = document.getElementById('region-grid');
  if (!grid) return;
  grid.innerHTML = '';
  for (const region of catalog.regions) {
    const card = document.createElement('div');
    card.className = 'region-card fade-in';
    card.onclick = () => showRegion(region.id);
    card.innerHTML = `
      <span class="rc-emoji">${region.emoji}</span>
      <div class="rc-name">${region.name}</div>
      <div class="rc-count">${region.songCount}곡</div>
      <div class="rc-desc">${region.description.substring(0, 100)}...</div>
    `;
    grid.appendChild(card);
  }
  observeFadeIns();
}

// === Navigation ===
function showHome() {
  document.getElementById('home-view').style.display = '';
  document.getElementById('region-view').style.display = 'none';
  const tlv = document.getElementById('timeline-view');
  if (tlv) tlv.style.display = 'none';
  window.scrollTo(0, 0);
}

function showRegion(regionId) {
  if (!catalog) return;
  const region = catalog.regions.find(r => r.id === regionId);
  if (!region) return;
  currentRegion = region;

  document.getElementById('home-view').style.display = 'none';
  document.getElementById('region-view').style.display = '';
  const tlv = document.getElementById('timeline-view');
  if (tlv) tlv.style.display = 'none';

  // Set hero
  document.getElementById('region-emoji').textContent = region.emoji;
  document.getElementById('region-name').textContent = region.name;
  document.getElementById('region-song-count').textContent = `${region.songCount}곡`;
  document.getElementById('region-description').textContent = region.description;

  // Korean-specific content
  const koreanContent = document.getElementById('korean-content');
  if (regionId === 'korean') {
    koreanContent.style.display = '';
  } else {
    koreanContent.style.display = 'none';
  }

  // Player title
  document.getElementById('player-title').textContent = `🎧 ${region.emoji} ${region.name} MIDI 플레이어`;
  document.getElementById('player-subtitle').textContent =
    `${region.songCount}곡 — 곡을 클릭하면 브라우저에서 바로 재생됩니다`;

  // Build player
  buildPlayerUI(region);

  window.scrollTo(0, 0);
  observeFadeIns();
}

// === Player UI ===
function buildPlayerUI(region) {
  const container = document.getElementById('midi-player-app');
  if (!container) return;

  allTracks = [];
  let html = `
    <div class="mp-controls">
      <div class="mp-now-playing">
        <div class="mp-title" id="mp-title">곡을 선택하세요</div>
        <div class="mp-sub" id="mp-sub"></div>
      </div>
      <div class="mp-buttons">
        <button id="mp-prev" class="mp-btn" onclick="playPrevTrack()">⏮</button>
        <button id="mp-play" class="mp-btn" disabled onclick="togglePlay()">▶ 재생</button>
        <button id="mp-stop" class="mp-btn" onclick="stopMidi()">⏹</button>
        <button id="mp-next" class="mp-btn" onclick="playNextTrack()">⏭</button>
        <div class="mp-progress-wrap" onclick="seekInPlayer(event)">
          <div class="mp-progress" id="mp-progress"></div>
        </div>
        <span class="mp-time" id="mp-time">0:00</span>
      </div>
    </div>
    <div class="mp-search">
      <input type="text" placeholder="이 지역에서 검색..." oninput="filterTracks(this.value)">
    </div>
    <div class="mp-catalog">
  `;

  let trackIdx = 0;
  for (const group of region.groups) {
    const groupTrackStart = trackIdx;
    html += `<div class="mp-suite">
      <div class="mp-suite-header" onclick="toggleSuite(this)">
        <span class="mp-arrow">▶</span> ${group.name}
        ${group.era ? `<span class="mp-era">${group.era}</span>` : ''}
      </div>
      <div class="mp-suite-list" style="display:none">`;

    for (const track of group.tracks) {
      const encodedFile = encodeURIComponent(track.file);
      const basePath = region.basePath;
      allTracks.push({
        file: track.file,
        title: track.title,
        group: group.name,
        basePath: basePath,
        index: trackIdx
      });
      html += `<div class="mp-track" data-idx="${trackIdx}" data-title="${track.title.toLowerCase()}" onclick="loadTrackByIndex(${trackIdx})">
        <span class="mp-track-icon">♪</span> ${track.title}
        <a href="${basePath}${encodedFile}" download class="mp-dl" title="다운로드" onclick="event.stopPropagation()">⬇</a>
      </div>`;
      trackIdx++;
    }
    html += `</div></div>`;
  }

  html += `</div>`;
  container.innerHTML = html;
}

function toggleSuite(el) {
  const list = el.nextElementSibling;
  const arrow = el.querySelector('.mp-arrow');
  if (list.style.display === 'none') {
    list.style.display = 'block';
    arrow.textContent = '▼';
  } else {
    list.style.display = 'none';
    arrow.textContent = '▶';
  }
}

function filterTracks(query) {
  query = query.toLowerCase().trim();
  document.querySelectorAll('.mp-track').forEach(el => {
    const title = el.getAttribute('data-title') || '';
    el.classList.toggle('hidden', query && !title.includes(query));
  });
}

// === Track Loading ===
async function loadTrackByIndex(idx) {
  if (idx < 0 || idx >= allTracks.length) return;
  currentTrackIndex = idx;
  const track = allTracks[idx];

  // Highlight active track
  document.querySelectorAll('.mp-track.active').forEach(t => t.classList.remove('active'));
  const el = document.querySelector(`.mp-track[data-idx="${idx}"]`);
  if (el) {
    el.classList.add('active');
    currentTrackEl = el;
    // Expand parent suite if collapsed
    const suiteList = el.closest('.mp-suite-list');
    if (suiteList && suiteList.style.display === 'none') {
      suiteList.style.display = 'block';
      const arrow = suiteList.previousElementSibling.querySelector('.mp-arrow');
      if (arrow) arrow.textContent = '▼';
    }
    // Scroll into view
    el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  stopMidi();

  const titleEl = document.getElementById('mp-title');
  const subEl = document.getElementById('mp-sub');
  const playBtn = document.getElementById('mp-play');
  const timeEl = document.getElementById('mp-time');

  titleEl.textContent = track.title;
  subEl.textContent = track.group;
  playBtn.disabled = true;
  timeEl.textContent = '로딩...';

  // Update bottom player
  showBottomPlayer(track.title, currentRegion ? currentRegion.name : '');

  try {
    const url = `${track.basePath}${encodeURIComponent(track.file)}`;
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    currentMidi = new Midi(arrayBuffer);
    playBtn.disabled = false;
    const dur = currentMidi.duration;
    timeEl.textContent = formatTime(0) + ' / ' + formatTime(dur);
    updateBottomTime(0, dur);
    // Auto-play
    playMidi();
  } catch (e) {
    timeEl.textContent = '로딩 실패';
    console.error(e);
  }
}

// === Playback ===
function togglePlay() {
  if (!currentMidi) return;
  if (isPlaying) {
    pauseMidi();
  } else {
    playMidi();
  }
}

async function playMidi() {
  if (!currentMidi) return;

  // Ensure audio context is started (requires user gesture)
  if (Tone.context.state !== 'running') {
    await Tone.start();
  }

  synths.forEach(s => s.dispose());
  synths = [];

  const now = Tone.now() + 0.1;
  startTime = now;

  currentMidi.tracks.forEach(track => {
    const synth = new Tone.PolySynth(Tone.Synth, {
      envelope: { attack: 0.02, decay: 0.1, sustain: 0.3, release: 0.8 },
      oscillator: { type: 'triangle8' }
    }).toDestination();
    synth.volume.value = volumeDb;
    synths.push(synth);

    track.notes.forEach(note => {
      synth.triggerAttackRelease(
        note.name,
        note.duration,
        note.time + now,
        note.velocity
      );
    });
  });

  isPlaying = true;
  updatePlayButton(true);
  Tone.Transport.start();

  const totalDur = currentMidi.duration;
  progressInterval = setInterval(() => {
    const elapsed = Tone.now() - startTime;
    const pct = Math.min(elapsed / totalDur * 100, 100);

    const mpProg = document.getElementById('mp-progress');
    const mpTime = document.getElementById('mp-time');
    if (mpProg) mpProg.style.width = pct + '%';
    if (mpTime) mpTime.textContent = formatTime(elapsed) + ' / ' + formatTime(totalDur);

    updateBottomProgress(pct);
    updateBottomTime(elapsed, totalDur);

    if (elapsed >= totalDur) {
      stopMidi();
      // Auto-next
      playNextTrack();
    }
  }, 200);
}

function pauseMidi() {
  synths.forEach(s => s.dispose());
  synths = [];
  isPlaying = false;
  clearInterval(progressInterval);
  updatePlayButton(false);
}

function stopMidi() {
  synths.forEach(s => s.dispose());
  synths = [];
  isPlaying = false;
  clearInterval(progressInterval);
  updatePlayButton(false);

  const mpProg = document.getElementById('mp-progress');
  const mpTime = document.getElementById('mp-time');
  const mpPlay = document.getElementById('mp-play');
  if (mpProg) mpProg.style.width = '0%';
  if (currentMidi && mpTime) {
    mpTime.textContent = '0:00 / ' + formatTime(currentMidi.duration);
  }
  if (mpPlay) mpPlay.disabled = !currentMidi;

  updateBottomProgress(0);
  if (currentMidi) updateBottomTime(0, currentMidi.duration);
}

function playNextTrack() {
  if (allTracks.length === 0) return;
  const next = (currentTrackIndex + 1) % allTracks.length;
  loadTrackByIndex(next);
}

function playPrevTrack() {
  if (allTracks.length === 0) return;
  const prev = currentTrackIndex <= 0 ? allTracks.length - 1 : currentTrackIndex - 1;
  loadTrackByIndex(prev);
}

function setVolume(val) {
  volumeDb = (val / 100) * 24 - 24; // 0→-24dB, 100→0dB
  synths.forEach(s => { s.volume.value = volumeDb; });
}

function seekInPlayer(e) {
  if (!currentMidi) return;
  const rect = e.currentTarget.getBoundingClientRect();
  const pct = (e.clientX - rect.left) / rect.width;
  // Restart at that position (simple approach: restart entire playback)
  const seekTime = pct * currentMidi.duration;
  if (isPlaying) {
    stopMidi();
    // Replay from offset
    playMidiFromOffset(seekTime);
  }
}

function seekTo(e) {
  seekInPlayer(e);
}

function playMidiFromOffset(offset) {
  if (!currentMidi) return;

  synths.forEach(s => s.dispose());
  synths = [];

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
        synth.triggerAttackRelease(
          note.name,
          note.duration,
          note.time - offset + now,
          note.velocity
        );
      }
    });
  });

  isPlaying = true;
  updatePlayButton(true);
  Tone.Transport.start();

  const totalDur = currentMidi.duration;
  progressInterval = setInterval(() => {
    const elapsed = Tone.now() - startTime;
    const pct = Math.min(elapsed / totalDur * 100, 100);

    const mpProg = document.getElementById('mp-progress');
    const mpTime = document.getElementById('mp-time');
    if (mpProg) mpProg.style.width = pct + '%';
    if (mpTime) mpTime.textContent = formatTime(elapsed) + ' / ' + formatTime(totalDur);

    updateBottomProgress(pct);
    updateBottomTime(elapsed, totalDur);

    if (elapsed >= totalDur) {
      stopMidi();
      playNextTrack();
    }
  }, 200);
}

// === UI Updates ===
function updatePlayButton(playing) {
  const mpPlay = document.getElementById('mp-play');
  const bpPlay = document.getElementById('bp-play');
  if (mpPlay) mpPlay.textContent = playing ? '⏸ 일시정지' : '▶ 재생';
  if (bpPlay) bpPlay.textContent = playing ? '⏸' : '▶';
}

function showBottomPlayer(title, regionName) {
  const bar = document.getElementById('bottom-player');
  bar.style.display = 'flex';
  document.body.classList.add('player-active');
  document.getElementById('bp-title').textContent = title;
  document.getElementById('bp-region').textContent = regionName;
}

function updateBottomProgress(pct) {
  const el = document.getElementById('bp-progress');
  if (el) el.style.width = pct + '%';
}

function updateBottomTime(elapsed, total) {
  const el = document.getElementById('bp-time');
  if (el) el.textContent = formatTime(elapsed);
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m + ':' + (s < 10 ? '0' : '') + s;
}

// === Global Search ===
function handleGlobalSearch(query) {
  const resultsEl = document.getElementById('global-search-results');
  if (!catalog || !query.trim()) {
    resultsEl.style.display = 'none';
    return;
  }

  query = query.toLowerCase().trim();
  const results = [];

  for (const region of catalog.regions) {
    for (const group of region.groups) {
      for (const track of group.tracks) {
        const titleMatch = track.title.toLowerCase().includes(query);
        const titleKoMatch = track.title_ko && track.title_ko.toLowerCase().includes(query);
        const countryEnMatch = track.country_en && track.country_en.toLowerCase().includes(query);
        const countryKoMatch = track.country_ko && track.country_ko.includes(query);
        if (titleMatch || titleKoMatch || countryEnMatch || countryKoMatch) {
          const subtitle = track.country_ko ? `${track.country_ko} (${track.country_en})` : '';
          results.push({
            title: track.title_ko ? `${track.title_ko} (${track.title})` : track.title,
            regionName: subtitle || region.name,
            regionId: region.id,
            emoji: region.emoji,
            file: track.file,
            group: group.name,
            origTitle: track.title
          });
        }
        if (results.length >= 20) break;
      }
      if (results.length >= 20) break;
    }
    if (results.length >= 20) break;
  }

  if (results.length === 0) {
    resultsEl.style.display = 'none';
    return;
  }

  resultsEl.style.display = '';
  resultsEl.innerHTML = results.map((r, i) => {
    const clickTitle = r.origTitle || r.title;
    return `<div class="search-result-item" onclick="searchResultClick('${r.regionId}', '${encodeURIComponent(clickTitle)}')">
      <span class="sr-emoji">${r.emoji}</span>
      <span class="sr-title">${r.title}</span>
      <span class="sr-region">${r.regionName}</span>
    </div>`;
  }).join('');
}

function searchResultClick(regionId, encodedTitle) {
  const title = decodeURIComponent(encodedTitle);
  document.getElementById('global-search-results').style.display = 'none';
  document.getElementById('global-search').value = '';

  // Navigate to region then find and play track
  showRegion(regionId);

  // Find track index
  const idx = allTracks.findIndex(t => t.title === title);
  if (idx >= 0) {
    setTimeout(() => loadTrackByIndex(idx), 100);
  }
}

// Close search results when clicking outside
document.addEventListener('click', (e) => {
  const searchArea = document.querySelector('.hero-search');
  const results = document.getElementById('global-search-results');
  if (searchArea && results && !searchArea.contains(e.target)) {
    results.style.display = 'none';
  }
});

// === Timeline View ===
function showTimeline() {
  document.getElementById('home-view').style.display = 'none';
  document.getElementById('region-view').style.display = 'none';
  document.getElementById('timeline-view').style.display = '';
  buildTimeline();
  window.scrollTo(0, 0);
}

function buildTimeline() {
  const container = document.getElementById('timeline-content');
  if (!container || !catalog || !catalog.timeline) return;

  const events = catalog.timeline.sort((a, b) => a.year - b.year);

  let html = '';
  let lastYear = null;

  for (const ev of events) {
    const yearStr = ev.year < 0 ? `BC ${Math.abs(ev.year)}` : `${ev.year}`;
    const sideClass = ev.side === 'korea' ? 'tl-left' : 'tl-right';
    const highlight = ev.title.includes('★') ? ' tl-highlight' : '';

    // Play button if track exists
    let playBtn = '';
    if (ev.trackTitle) {
      const escaped = ev.trackTitle.replace(/'/g, "\\'");
      playBtn = `<button class="tl-play-btn" onclick="timelinePlay('${ev.regionId}', '${escaped}')">▶ 듣기</button>`;
    }

    html += `
      <div class="tl-item ${sideClass}${highlight}">
        <div class="tl-year">${yearStr}</div>
        <div class="tl-card">
          <div class="tl-side-label">${ev.side === 'korea' ? '🇰🇷 한국' : '🌍 세계'}</div>
          <h3 class="tl-title">${ev.title}</h3>
          <p class="tl-desc">${ev.desc}</p>
          ${playBtn}
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
  observeFadeIns();
}

async function timelinePlay(regionId, trackTitle) {
  if (!catalog) return;
  const region = catalog.regions.find(r => r.id === regionId);
  if (!region) return;

  // Find the track's file and basePath
  let targetFile = null;
  let basePath = region.basePath;
  for (const group of region.groups) {
    for (const track of group.tracks) {
      if (track.title === trackTitle) {
        targetFile = track.file;
        break;
      }
    }
    if (targetFile) break;
  }
  if (!targetFile) return;

  // Ensure audio context
  if (Tone.context.state !== 'running') {
    await Tone.start();
  }

  // Stop current playback
  stopMidi();

  // Show bottom player
  showBottomPlayer(trackTitle, region.name);

  // Load and play directly (no page navigation)
  try {
    const url = `${basePath}${encodeURIComponent(targetFile)}`;
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    currentMidi = new Midi(arrayBuffer);
    updateBottomTime(0, currentMidi.duration);
    playMidi();
  } catch (e) {
    console.error('Timeline play error:', e);
  }
}

// === Init ===
document.addEventListener('DOMContentLoaded', loadCatalog);
