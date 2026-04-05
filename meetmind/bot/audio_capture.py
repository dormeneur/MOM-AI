"""
Audio Capture — captures meeting audio via virtual audio device + FFmpeg.

Produces 5-second WAV chunks (16kHz mono PCM) and POSTs them to the backend API.

Platform notes:
- Linux:  PulseAudio virtual sink
- macOS:  BlackHole virtual audio device
- Windows: VB-CABLE or WASAPI loopback
"""

import os
import glob
import asyncio
import logging

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    Captures audio from a virtual audio sink using FFmpeg,
    segments into 5-second WAV chunks, and uploads each chunk.
    """

    def __init__(self, session_id: str, api_base_url: str = "http://localhost:8000"):
        self.session_id = session_id
        self.api_base_url = api_base_url
        self._process = None
        self._running = False
        self._chunk_dir = os.path.join("audio_chunks", session_id)

    async def start(self):
        """Start FFmpeg subprocess and begin uploading chunks."""
        os.makedirs(self._chunk_dir, exist_ok=True)
        self._running = True

        # Determine platform-specific audio input
        import platform
        system = platform.system()

        if system == "Linux":
            input_args = ['-f', 'pulse', '-i', 'virtual_sink.monitor']
        elif system == "Darwin":
            input_args = ['-f', 'avfoundation', '-i', ':BlackHole 2ch']
        elif system == "Windows":
            # Uses DirectShow with VB-CABLE or default loopback
            input_args = ['-f', 'dshow', '-i', 'audio=CABLE Output (VB-Audio Virtual Cable)']
        else:
            input_args = ['-f', 'pulse', '-i', 'default']

        chunk_pattern = os.path.join(self._chunk_dir, "chunk_%04d.wav")

        cmd = [
            'ffmpeg', '-y',
            *input_args,
            '-ar', '16000',         # 16kHz sample rate (Whisper requirement)
            '-ac', '1',             # mono
            '-f', 'segment',
            '-segment_time', '5',   # 5-second chunks
            '-segment_format', 'wav',
            chunk_pattern,
        ]

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            logger.info(f"FFmpeg audio capture started for session {self.session_id}")
        except FileNotFoundError:
            logger.error("FFmpeg not found. Install ffmpeg and ensure it's on PATH.")
            return

        # Start upload watcher
        await self._upload_chunks()

    async def _upload_chunks(self):
        """Watch for new chunk files and POST them to the API."""
        import httpx

        uploaded = set()

        while self._running:
            await asyncio.sleep(2)
            pattern = os.path.join(self._chunk_dir, "chunk_*.wav")
            files = sorted(glob.glob(pattern))

            for filepath in files:
                if filepath in uploaded:
                    continue

                # Wait for file to be fully written
                try:
                    size1 = os.path.getsize(filepath)
                    await asyncio.sleep(0.5)
                    size2 = os.path.getsize(filepath)
                    if size1 != size2:
                        continue  # Still being written
                except OSError:
                    continue

                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        with open(filepath, 'rb') as f:
                            resp = await client.post(
                                f"{self.api_base_url}/api/sessions/{self.session_id}/audio",
                                files={"audio_file": (os.path.basename(filepath), f, "audio/wav")},
                            )
                    if resp.status_code == 200:
                        uploaded.add(filepath)
                        logger.info(f"Uploaded chunk: {os.path.basename(filepath)}")
                    else:
                        logger.warning(f"Chunk upload failed ({resp.status_code}): {filepath}")
                except Exception as e:
                    logger.error(f"Chunk upload error: {e}")

    async def stop(self):
        """Stop the FFmpeg process."""
        self._running = False
        if self._process:
            self._process.terminate()
            await self._process.wait()
            logger.info("Audio capture stopped")
