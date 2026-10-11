// TrailPacer AI Web Client Logic

let currentWorkout = null;
let currentActivity = 'fartlek_run';
let currentDuration = 30;
let currentLevel = 'intermediate';

// Audio context for offline audio transition chimes
let audioCtx = null;
function playBeep(freq = 587.33, duration = 0.25) {
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (e) {
    console.warn("Audio cue suppressed:", e);
  }
}

// Elements
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const modelBadge = document.getElementById('modelBadge');

const durationInput = document.getElementById('durationInput');
const durationDisplay = document.getElementById('durationDisplay');
const generateBtn = document.getElementById('generateBtn');
const btnSpinner = document.getElementById('btnSpinner');

const idleState = document.getElementById('idleState');
const loadingState = document.getElementById('loadingState');
const workoutContent = document.getElementById('workoutContent');

const pillActivity = document.getElementById('pillActivity');
const pillDuration = document.getElementById('pillDuration');
const workoutTitle = document.getElementById('workoutTitle');
const terrainText = document.getElementById('terrainText');
const blocksList = document.getElementById('blocksList');
const latencyTag = document.getElementById('latencyTag');
const copyJsonBtn = document.getElementById('copyJsonBtn');
const startWorkoutBtn = document.getElementById('startWorkoutBtn');

// HUD Elements
const playerHUD = document.getElementById('playerHUD');
const closeHudBtn = document.getElementById('closeHudBtn');
const hudPhaseBadge = document.getElementById('hudPhaseBadge');
const hudTimerDigits = document.getElementById('hudTimerDigits');
const hudInstructionText = document.getElementById('hudInstructionText');
const hudRpeNumber = document.getElementById('hudRpeNumber');
const hudRpeFill = document.getElementById('hudRpeFill');
const prevBlockBtn = document.getElementById('prevBlockBtn');
const playPauseBtn = document.getElementById('playPauseBtn');
const nextBlockBtn = document.getElementById('nextBlockBtn');

// HUD State
let hudActiveIndex = 0;
let hudSecondsLeft = 0;
let hudTimerInterval = null;
let hudIsPaused = false;

// Check server status
async function checkStatus() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) throw new Error('Status endpoint unavailable');
    const data = await res.json();
    modelBadge.textContent = data.model || 'qwen2.5:0.5b';
    if (data.ollama_connected) {
      statusDot.className = 'status-indicator live';
      statusText.textContent = 'Ollama Connected';
    } else {
      statusDot.className = 'status-indicator';
      statusDot.style.background = '#f59e0b';
      statusText.textContent = 'Offline Fallback Cache Ready';
    }
  } catch (err) {
    statusDot.className = 'status-indicator';
    statusText.textContent = 'Server Standby';
  }
}

// Activity selection
document.querySelectorAll('.activity-card').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.activity-card').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentActivity = btn.dataset.activity;
  });
});

// Duration slider & chips
durationInput.addEventListener('input', (e) => {
  currentDuration = parseInt(e.target.value, 10);
  durationDisplay.textContent = `${currentDuration} min`;
  syncChips(currentDuration);
});

document.querySelectorAll('.quick-chips .chip').forEach(chip => {
  chip.addEventListener('click', () => {
    currentDuration = parseInt(chip.dataset.min, 10);
    durationInput.value = currentDuration;
    durationDisplay.textContent = `${currentDuration} min`;
    syncChips(currentDuration);
  });
});

function syncChips(val) {
  document.querySelectorAll('.quick-chips .chip').forEach(c => {
    c.classList.toggle('active', parseInt(c.dataset.min, 10) === val);
  });
}

// Level segmented control
document.querySelectorAll('.segment-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentLevel = btn.dataset.level;
  });
});

// Format activity name
function formatActivity(name) {
  return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

// Render Workout Cards
function renderWorkout(workout, latency = null) {
  currentWorkout = workout;
  pillActivity.textContent = formatActivity(workout.activity_type);
  pillDuration.textContent = `${workout.target_duration_minutes} min`;
  workoutTitle.textContent = workout.title;
  terrainText.textContent = workout.terrain_suggestion || 'Adaptive outdoor terrain';

  if (latency) {
    latencyTag.textContent = `⚡ Generated in ${latency}s`;
  } else {
    latencyTag.textContent = `⚡ Pre-spec verified`;
  }

  blocksList.innerHTML = '';
  workout.blocks.forEach((block, index) => {
    const card = document.createElement('div');
    card.className = 'block-card';

    const rpePercent = Math.min(Math.max((block.target_rpe_1_to_10 / 10) * 100, 10), 100);
    let rpeColor = '#10b981';
    if (block.target_rpe_1_to_10 >= 7) rpeColor = '#ef4444';
    else if (block.target_rpe_1_to_10 >= 4) rpeColor = '#f59e0b';

    card.innerHTML = `
      <div class="block-header">
        <span class="block-badge ${block.phase}">${block.phase.replace('_', ' ')}</span>
        <span class="block-duration">${block.duration_minutes} min</span>
      </div>
      <p class="block-instruction">${block.instruction}</p>
      <div class="block-rpe-bar">
        <span class="rpe-tag">RPE ${block.target_rpe_1_to_10}/10</span>
        <div class="rpe-meter">
          <div class="rpe-fill" style="width: ${rpePercent}%; background: ${rpeColor};"></div>
        </div>
      </div>
    `;
    blocksList.appendChild(card);
  });

  idleState.style.display = 'none';
  loadingState.style.display = 'none';
  playerHUD.style.display = 'none';
  workoutContent.style.display = 'block';
}

// Generate Workout Action
async function handleGenerate() {
  generateBtn.disabled = true;
  btnSpinner.style.display = 'block';
  document.querySelector('.btn-text').textContent = 'Synthesizing...';
  
  workoutContent.style.display = 'none';
  idleState.style.display = 'none';
  loadingState.style.display = 'block';

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        activity: currentActivity,
        duration: currentDuration,
        fitness_level: currentLevel
      })
    });

    const data = await res.json();
    if (data.success && data.workout) {
      renderWorkout(data.workout, data.latency_seconds);
    } else {
      alert(`Generation issue: ${data.error || 'Check local Ollama daemon'}`);
      workoutContent.style.display = 'block';
      loadingState.style.display = 'none';
    }
  } catch (err) {
    console.error(err);
    alert('Could not reach TrailPacer local server.');
    workoutContent.style.display = 'block';
    loadingState.style.display = 'none';
  } finally {
    generateBtn.disabled = false;
    btnSpinner.style.display = 'none';
    document.querySelector('.btn-text').textContent = 'Generate Workout';
  }
}

generateBtn.addEventListener('click', handleGenerate);

// Copy JSON
copyJsonBtn.addEventListener('click', () => {
  if (!currentWorkout) return;
  navigator.clipboard.writeText(JSON.stringify(currentWorkout, null, 2)).then(() => {
    const originalText = copyJsonBtn.innerHTML;
    copyJsonBtn.innerHTML = `✓ Copied!`;
    setTimeout(() => { copyJsonBtn.innerHTML = originalText; }, 2000);
  });
});

// Interactive Companion HUD Player
function startHUD() {
  if (!currentWorkout || !currentWorkout.blocks.length) return;
  workoutContent.style.display = 'none';
  playerHUD.style.display = 'block';
  hudActiveIndex = 0;
  loadHUDBlock(0);
}

function loadHUDBlock(index) {
  if (!currentWorkout.blocks[index]) return;
  hudActiveIndex = index;
  const block = currentWorkout.blocks[index];
  
  hudPhaseBadge.textContent = block.phase.replace('_', ' ').toUpperCase();
  hudInstructionText.textContent = block.instruction;
  hudRpeNumber.textContent = `RPE ${block.target_rpe_1_to_10} / 10`;
  hudRpeFill.style.width = `${block.target_rpe_1_to_10 * 10}%`;

  hudSecondsLeft = block.duration_minutes * 60;
  updateTimerDisplay();
  startTimer();
  playBeep(440, 0.2); // Phase change chime
}

function updateTimerDisplay() {
  const mins = Math.floor(hudSecondsLeft / 60);
  const secs = hudSecondsLeft % 60;
  hudTimerDigits.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function startTimer() {
  clearInterval(hudTimerInterval);
  hudIsPaused = false;
  playPauseBtn.textContent = 'Pause';
  hudTimerInterval = setInterval(() => {
    if (hudSecondsLeft > 0) {
      hudSecondsLeft--;
      updateTimerDisplay();
      if (hudSecondsLeft === 3 || hudSecondsLeft === 2 || hudSecondsLeft === 1) {
        playBeep(520, 0.1); // Countdown beep
      }
    } else {
      // Advance to next block
      if (hudActiveIndex < currentWorkout.blocks.length - 1) {
        loadHUDBlock(hudActiveIndex + 1);
      } else {
        clearInterval(hudTimerInterval);
        playBeep(880, 0.6); // Finish chime
        alert('Outdoor Workout Complete! Great effort.');
        exitHUD();
      }
    }
  }, 1000);
}

function exitHUD() {
  clearInterval(hudTimerInterval);
  playerHUD.style.display = 'none';
  workoutContent.style.display = 'block';
}

startWorkoutBtn.addEventListener('click', startHUD);
closeHudBtn.addEventListener('click', exitHUD);

playPauseBtn.addEventListener('click', () => {
  if (hudIsPaused) {
    startTimer();
  } else {
    clearInterval(hudTimerInterval);
    hudIsPaused = true;
    playPauseBtn.textContent = 'Resume';
  }
});

prevBlockBtn.addEventListener('click', () => {
  if (hudActiveIndex > 0) loadHUDBlock(hudActiveIndex - 1);
});

nextBlockBtn.addEventListener('click', () => {
  if (hudActiveIndex < currentWorkout.blocks.length - 1) {
    loadHUDBlock(hudActiveIndex + 1);
  }
});

// Initialize on page load
checkStatus();

// Automatically generate or populate default workout for immediate interaction
(async function initDefault() {
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ activity: 'fartlek_run', duration: 30, fitness_level: 'intermediate' })
    });
    const data = await res.json();
    if (data.workout) renderWorkout(data.workout, data.latency_seconds);
  } catch (e) {
    console.warn("Initial generation defaulted:", e);
  }
})();
