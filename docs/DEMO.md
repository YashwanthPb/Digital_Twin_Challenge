# Narrated prototype walkthrough

**Video:** [pulsetwin-demo.mp4](../artifacts/pulsetwin-demo.mp4) — approximately 18 minutes 53 seconds, 1280×720, H.264 video, AAC audio, embedded English captions.

**Captions:** [demo.srt](../artifacts/demo.srt). **Chapter timing:** [demo-timeline.json](../artifacts/demo-timeline.json). **Transcript:** [demo-script.md](demo-script.md).

This is a synthesized-voice presentation and narrated walkthrough of actual application captures, not a recording of a person or a live clinical session. Caption sentence timing is approximate. Screenshots are produced by driving the real app in Chromium; slides and narration explain implemented features, results and limitations.

## Required publication step

The submission form requires a 15–20 minute **Unlisted YouTube** video linked in README. The local MP4 is ready for upload, but no authorized YouTube tool or account credential is available in this environment. A GitHub-hosted MP4 does not replace the required YouTube URL. Upload the file as Unlisted, add the actual watch URL to README, and test playback signed out. No YouTube upload has been claimed.

Suggested video title: **PulseTwin | Personal Blood-Pressure Digital Twin | Digital Twin Challenge 2026**.

Suggested description:

> PulseTwin is an open-source research prototype combining personal Bayesian regression, a Kalman residual state, hypothetical lifestyle scenarios and uncertainty visualization. This walkthrough uses entirely synthetic data. No clinical validation, diagnosis or treatment recommendation is claimed. Code and documents: https://github.com/YashwanthPb/Digital_Twin_Challenge

## Regenerate

Install `requirements-lock.txt`. System prerequisites: Chromium, Poppler (`pdftoppm`), Open Sans fonts, FFmpeg and eSpeak NG. On Debian, those are available as `chromium poppler-utils fonts-open-sans ffmpeg espeak-ng`. Install system packages through your platform's approved package manager; keep package verification enabled.

With the application running on port 8000:

```bash
.venv/bin/python scripts/capture_demo.py
.venv/bin/python scripts/build_documents.py
.venv/bin/python scripts/build_video.py
```

Set `CHROMIUM_PATH` for a different Chromium executable, or `ESPEAK_BIN` for a different eSpeak NG executable. The document generator uses Open Sans from `/usr/share/fonts/truetype/open-sans/`. In the prepared cloud instance, eSpeak packages were downloaded using signed Debian package metadata and extracted outside the repository. To use that retained installation:

```bash
LD_LIBRARY_PATH=/workspace/pulsetwin-tools/root/usr/lib/x86_64-linux-gnu \
ESPEAK_DATA_PATH=/workspace/pulsetwin-tools/root/usr/lib/x86_64-linux-gnu/espeak-ng-data \
ESPEAK_BIN=/workspace/pulsetwin-tools/root/usr/bin/espeak-ng \
.venv/bin/python scripts/build_video.py
```

The renderer enforces a 900–1200 second total duration. Source slides and narration are in `scripts/demo_content.py`. Intermediate WAVs, PNG slides and video segments are ignored by Git; the final MP4 is explicitly included.
