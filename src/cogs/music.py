from collections import deque
from typing import Optional

import discord
from discord.ext import commands
import static_ffmpeg
from yt_dlp import YoutubeDL

OPTIONS_YOUTUBEDL = {
    "format": "bestaudio",
    "noplaylist": "True",
    "quiet": "True"
}
OPTIONS_FFMPEG = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.music_queue = deque()
        self.voice_client: Optional[discord.VoiceClient] = None
        self.is_playing = False
        self.is_paused = False
        self.song_currently_played = None

    @staticmethod
    def yt_search(query: str) -> Optional[tuple[str, str]]:
        with YoutubeDL(OPTIONS_YOUTUBEDL) as ytdl:
            info = ytdl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
            return info["title"], info["url"]

    def play_next(self) -> None:
        if not self.music_queue:
            self.is_playing = False
            self.song_currently_played = None
            return

        self.is_playing = True
        title, source_url = self.music_queue.popleft()
        self.song_currently_played = title
        self.voice_client.play(discord.FFmpegPCMAudio(source_url, **OPTIONS_FFMPEG), after=lambda e: self.play_next())

    @commands.command(aliases=["p"], help="Play music | <song name or url>")
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        voice_state = ctx.author.voice
        if voice_state is None:
            await ctx.send("You must be in a voice channel.")
            return

        if self.voice_client is None:
            self.voice_client = await voice_state.channel.connect(self_deaf=True)

        if voice_state.channel != self.voice_client.channel:
            await self.voice_client.move_to(voice_state.channel)

        self.music_queue.append(self.yt_search(query))

        if self.is_playing or self.is_paused:
            return

        self.play_next()

    @commands.command(help="Pause playing music | No arguments required")
    async def pause(self, ctx: commands.Context) -> None:
        if self.voice_client is None:
            return

        self.is_paused = True
        self.voice_client.pause()

    @commands.command(aliases=["resume"], help="Unpause paused music | No arguments required")
    async def unpause(self, ctx: commands.Context) -> None:
        if self.voice_client is None:
            return

        self.is_paused = False
        self.voice_client.resume()

    @commands.command(aliases=["leave"], help="Stop playing music and clear the music queue | No arguments required")
    async def stop(self, ctx: commands.Context) -> None:
        if self.voice_client is None:
            return

        self.music_queue.clear()
        self.voice_client.stop()
        await self.voice_client.disconnect()

    @commands.command(help="Clear the music queue | No arguments required")
    async def clear(self, ctx: commands.Context) -> None:
        if self.voice_client is None:
            return

        self.music_queue.clear()

    @commands.command(aliases=["q"], help="Print the music queue | No arguments required")
    async def queue(self, ctx: commands.Context) -> None:
        if self.song_currently_played is None:
            await ctx.send("The music queue is empty")
            return

        await ctx.send(f"Currently playing: {self.song_currently_played}")

        if self.music_queue is None:
            return

        output_str = '\n'.join(f"{i: >4}. {title}" for i, (title, _) in enumerate(self.music_queue, 1))

        if len(output_str) <= 2000:
            await ctx.send(output_str)
            return

        for chunk in (output_str[i:i + 2000] for i in range(0, len(output_str), 2000)):
            await ctx.send(chunk)


async def setup(bot: commands.Bot):
    static_ffmpeg.add_paths()
    await bot.add_cog(Music(bot))
