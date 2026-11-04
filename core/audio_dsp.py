# core/audio_dsp.py
import asyncio
import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class AudioDSP:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.fifo_path = f"/tmp/nobi_fifo_{user_id}.pcm"
        self.sink_name = f"FightSink_{user_id}"
        self.ffmpeg_process = None

    async def setup_sink(self):
        logger.info(f"[DSP] Setting up sink for {self.user_id}")
        # Load pulseaudio null sink
        await asyncio.create_subprocess_shell(
            f"pactl load-module module-null-sink sink_name={self.sink_name} sink_properties=device.description={self.sink_name}",
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if not os.path.exists(self.fifo_path):
            os.mkfifo(self.fifo_path)

    async def start_ffmpeg(self, effects: dict):
        filter_chain = []
        if effects.get("level"): filter_chain.append(f"volume={effects['level']/100}")
        if effects.get("bass"): filter_chain.append(f"bass=g={effects['bass']}")
        if effects.get("treble"): filter_chain.append(f"treble=g={effects['treble']}")
        if effects.get("overdrive"): filter_chain.append(f"overdrive={effects['overdrive']}")
        
        af_string = ",".join(filter_chain) if filter_chain else "anull"
        
        cmd = f"ffmpeg -y -f s16le -ac 2 -ar 48000 -i {self.fifo_path} -af '{af_string}' -f pulse {self.sink_name}"
        
        self.ffmpeg_process = await asyncio.create_subprocess_shell(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        logger.info(f"[DSP] FFmpeg started for {self.user_id}")

    async def stop(self):
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
        await asyncio.create_subprocess_shell(f"pactl unload-module {self.sink_name}", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(self.fifo_path):
            os.remove(self.fifo_path)
