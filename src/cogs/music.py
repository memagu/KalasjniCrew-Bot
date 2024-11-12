import asyncio
from collections import deque
from dataclasses import dataclass, field
import re
from typing import Optional

import discord
from discord.ext import commands
import static_ffmpeg
from yt_dlp import YoutubeDL

OPTIONS_FFMPEG = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


class _YouTube:
    OPTIONS = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True
    }

    @staticmethod
    def is_valid_url(url: str) -> bool:
        youtube_url_regex = re.compile(r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+")
        return youtube_url_regex.match(url) is not None

    @classmethod
    def search(cls, query: str) -> tuple[tuple[str, str]]:
        with YoutubeDL(cls.OPTIONS) as ydl:
            ydl._ies = {
                "Youtube": ydl.get_info_extractor("Youtube"),
                "YoutubeSearch": ydl.get_info_extractor("YoutubeSearch"),
                "YoutubeTab": ydl.get_info_extractor("YoutubeTab"),
            }

            query = query if cls.is_valid_url(query) else "ytsearch1:" + query

            result = ydl.extract_info(query, download=False)

            if "entries" in result:
                return tuple((entry["title"], entry["url"]) for entry in result["entries"] if entry is not None)

            return ((result["title"], result["url"]),)

@dataclass
class MusicInstance:
    voice_client: Optional[discord.VoiceClient] = None
    active_music: Optional[str] = None
    music_queue: deque[tuple[str, str]] = field(default_factory=deque)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.music_instances: dict[int, MusicInstance] = {}

    async def play_next(self, guild_id: int) -> None:
        music_instance = self.music_instances[guild_id]

        if not music_instance.music_queue:
            await music_instance.voice_client.disconnect()
            del self.music_instances[guild_id]
            return

        title, source_url = music_instance.music_queue.popleft()
        music_instance.active_music = title
        music_instance.voice_client.play(
            discord.FFmpegPCMAudio(source_url, **OPTIONS_FFMPEG),
            after=lambda _: asyncio.run_coroutine_threadsafe(
                self.play_next(guild_id),
                self.bot.loop
            )
        )

    @commands.command(aliases=["p"], help="Play music | <song name or url>")
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        voice_state = ctx.author.voice
        if voice_state is None:
            await ctx.send("You must be in a voice channel")
            return

        if ctx.guild.id not in self.music_instances:
            self.music_instances[ctx.guild.id] = MusicInstance(
                voice_client=await voice_state.channel.connect(self_deaf=True),
            )
            self.music_instances[ctx.guild.id].voice_client.play(
                discord.FFmpegPCMAudio("../assets/audio/obi_wan_hello_there.mp3")
            )

        music_instance = self.music_instances[ctx.guild.id]

        if music_instance.voice_client.channel != voice_state.channel:
            await music_instance.voice_client.move_to(voice_state.channel)

        songs = _YouTube.search(query)
        music_instance.music_queue.extend(songs)
        for title, *_ in songs:
            await ctx.send(f"Added {title} to the queue")

        if music_instance.active_music is not None:
            return

        await self.play_next(ctx.guild.id)

    @commands.command(help="Skip the song currently being played | <amount (OPTIONAL)>")
    async def skip(self, ctx: commands.Context, amount: int = 1) -> None:
        music_instance = self.music_instances[ctx.guild.id]

        amount = max(min(amount - 1, len(music_instance.music_queue)), 0)
        for _ in range(amount):
            music_instance.music_queue.popleft()

        music_instance.voice_client.stop()

    @commands.command(aliases=["leave"], help="Stop playing music and clear the music queue | No arguments required")
    async def stop(self, ctx: commands.Context) -> None:
        if ctx.guild.id not in self.music_instances:
            return

        music_instance = self.music_instances[ctx.guild.id]

        music_instance.music_queue.clear()
        music_instance.voice_client.stop()

    @commands.command(help="Pause playing music | No arguments required")
    async def pause(self, ctx: commands.Context) -> None:
        if ctx.guild.id in self.music_instances:
            self.music_instances[ctx.guild.id].voice_client.pause()

    @commands.command(aliases=["resume"], help="Unpause paused music | No arguments required")
    async def unpause(self, ctx: commands.Context) -> None:
        if ctx.guild.id in self.music_instances:
            self.music_instances[ctx.guild.id].voice_client.resume()

    @commands.command(help="Clear the music queue | No arguments required")
    async def clear(self, ctx: commands.Context) -> None:
        if ctx.guild.id in self.music_instances:
            self.music_instances[ctx.guild.id].music_queue.clear()

    @commands.command(help="Remove a song from the music queue | <queue_position>")
    async def remove(self, ctx: commands.Context, queue_position: int) -> None:
        if ctx.guild.id not in self.music_instances:
            return

        music_instance = self.music_instances[ctx.guild.id]

        queue_position = min(len(music_instance.music_queue) - 1,
                             max(-len(music_instance.music_queue), queue_position - 1))

        title, _ = music_instance.music_queue[queue_position]
        del music_instance.music_queue[queue_position]

        await ctx.send(f"Removed {title} from the playlist")

    @commands.command(aliases=["q"], help="Print the music queue | No arguments required")
    async def queue(self, ctx: commands.Context) -> None:
        if ctx.guild.id not in self.music_instances:
            return

        music_instance = self.music_instances[ctx.guild.id]

        if music_instance.active_music is None:
            await ctx.send("The music queue is empty")
            return

        await ctx.send(f"Currently playing: {music_instance.active_music}")

        if not music_instance.music_queue:
            return

        output_str = "\n".join(f"|{i: >4}. {title}" for i, (title, _) in enumerate(music_instance.music_queue, 1))

        if len(output_str) <= 2000:
            await ctx.send(output_str)
            return

        for chunk in (output_str[i:i + 2000] for i in range(0, len(output_str), 2000)):
            await ctx.send(chunk)

    @commands.command(help="Change the position of a song in the queue | <old_index> <new_index>")
    async def move(self, ctx: commands.Context, old_index: int, new_index: int) -> None:
        if ctx.guild.id not in self.music_instances:
            return

        music_instance = self.music_instances[ctx.guild.id]
        music_queue = music_instance.music_queue

        if not music_queue:
            return

        old_index -= 1
        new_index -= 1

        if not (0 <= old_index < len(music_queue) and 0 <= new_index < len(music_queue)):
            await ctx.send(f"Both indices must lie in the range: {1}-{len(music_queue)}")
            return

        title, source_url = music_queue[old_index]

        music_queue.insert(new_index, (title, source_url))
        del music_queue[old_index + (old_index >= new_index)]

        await ctx.send(f"Successfully moved {title} to position {new_index + 1} in the queue")

    @commands.command(help="Search for music | <song name or url>")
    async def search(self, ctx: commands.Context, *, query: str) -> None:
        output_str = "\n".join(f"{title}: {url}" for title, url in _YouTube.search(query))

        if len(output_str) <= 2000:
            await ctx.send(output_str)
            return

        for chunk in (output_str[i:i + 2000] for i in range(0, len(output_str), 2000)):
            await ctx.send(chunk)


async def setup(bot: commands.Bot):
    static_ffmpeg.add_paths()
    await bot.add_cog(Music(bot))
