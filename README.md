# TrailPacer AI 🌲🏃‍♂️

**TrailPacer AI** is an offline outdoor workout companion powered by local AI. It synthesizes structured, adaptive training sessions for trail runners, hikers, and outdoor fitness enthusiasts in under 5 seconds—with zero internet connectivity required and minimal screen interaction time (< 15 seconds).

---

## ✨ Features

- **100% Offline:** Runs completely on your device using open-weight local models (Llama 3.2 via Ollama). No cloud servers, no subscriptions, and absolute privacy.
- **Fast Generation:** Generates complete phased workouts in under 5 seconds on modern laptops and Apple Silicon.
- **Structured Phases:** Every session is broken down into structured warmup, main effort, and cooldown blocks with target RPE (Rate of Perceived Exertion) and terrain cues.
- **Built-in Offline Resilience:** Automatically serves pre-calibrated workouts from local cache if the AI model is offline or busy.

---

## 🏃 Supported Activities

- **Trail Walk (`trail_walk`)**: Low-impact aerobic power walking and recovery hikes on variable terrain.
- **Fartlek Run (`fartlek_run`)**: Speed-play running utilizing natural trail landmarks for surging and recovery intervals.
- **Rucking (`rucking`)**: Weighted backpack endurance sessions with posture and cadence pacing.
- **Interval Sprints (`interval_sprints`)**: High-intensity hill and flat repeats for explosive power and conditioning.

---

## 🚀 Getting Started

### 1. Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) (for local model inference)

### 2. Installation

Clone the repository and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Local Model Setup

Download the ultra-lightweight (~398 MB) model:

```bash
# Pull the ultra-lightweight, sub-second model
ollama pull qwen2.5:0.5b
```

*(Note: You can also use other models such as `llama3.2:1b` or `llama3.2:3b` by setting the `TRAILPACER_MODEL` environment variable).*


---

## 💡 Usage


### 1. Launch the Web UI (Recommended)

Start the local outdoor companion app and open it in your browser:

```bash
python -m src.app
```
Then visit **[http://localhost:8000](http://localhost:8000)**.

The Web UI features:
- **One-click Activity Selector**: Trail Walk, Fartlek Run, Rucking, and Interval Sprints.
- **Duration & Level Tuning**: Fast slider and quick-select duration chips.
- **Interactive Workout Pacer (HUD)**: Live countdown timer, phase transition chimes (via Web Audio), block instructions, and visual RPE gauge.
- **Copy & Export**: One-click JSON export.

---

### 2. Command Line Interface (CLI)

Run TrailPacer AI directly from the terminal:

```bash
python -m src.agent <activity_type> <duration_minutes> <fitness_level>
```


### Arguments:
- **`activity_type`**: `trail_walk` | `fartlek_run` | `rucking` | `interval_sprints`
- **`duration_minutes`**: Workout duration in minutes (e.g. `20`, `30`, `45`, `60`)
- **`fitness_level`**: `beginner` | `intermediate` | `advanced`

### Examples:

```bash
# 30-minute intermediate fartlek run
python -m src.agent fartlek_run 30 intermediate

# 45-minute beginner rucking session
python -m src.agent rucking 45 beginner

# 20-minute advanced interval sprints
python -m src.agent interval_sprints 20 advanced
```

### Example Workout Output:

```json
{
  "title": "Open Trail Landmark Fartlek",
  "activity_type": "fartlek_run",
  "target_duration_minutes": 30,
  "terrain_suggestion": "Undulating park loop or packed dirt trail",
  "blocks": [
    {
      "phase": "warmup",
      "duration_minutes": 5,
      "instruction": "Gentle jog with high knees and butt kicks",
      "target_rpe_1_to_10": 3
    },
    {
      "phase": "main_set",
      "duration_minutes": 20,
      "instruction": "Surge hard between trail markers (benches/trees), jog easy to recover",
      "target_rpe_1_to_10": 7
    },
    {
      "phase": "cooldown",
      "duration_minutes": 5,
      "instruction": "Slow jog into walk, followed by hamstring and hip flexor stretches",
      "target_rpe_1_to_10": 2
    }
  ]
}
```