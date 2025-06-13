import asyncio
from collections import deque
from dataclasses import dataclass, field
import re
from typing import Optional

from discord import ApplicationContext, Bot, Cog, FFmpegPCMAudio, Option, VoiceClient, slash_command
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
    async def search(cls, query: str) -> tuple[tuple[str, str]]:
        def _extract():
            with YoutubeDL(cls.OPTIONS) as ydl:
                ydl._ies = {
                    "Youtube": ydl.get_info_extractor("Youtube"),
                    "YoutubeSearch": ydl.get_info_extractor("YoutubeSearch"),
                    "YoutubeTab": ydl.get_info_extractor("YoutubeTab"),
                }
                search_query = query if cls.is_valid_url(query) else "ytsearch1:" + query
                return ydl.extract_info(search_query, download=False)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _extract)

        if "entries" in result:
            return tuple(
                (entry["title"], entry["url"]) for entry in result["entries"]
                if entry and "title" in entry and "url" in entry
            )

        return ((result["title"], result["url"]),)


@dataclass
class MusicInstance:
    voice_client: Optional[VoiceClient] = None
    active_music: Optional[str] = None
    music_queue: deque[tuple[str, str]] = field(default_factory=deque)


class Music(Cog):
    def __init__(self, bot: Bot):
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
            FFmpegPCMAudio(source_url, **OPTIONS_FFMPEG),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(guild_id),
                self.bot.loop
            ) if e is None else print(f"Error: {e}")
        )

    @slash_command(description="Play music | <track name or URL>")
    async def play(
        self,
        ctx: ApplicationContext,
        query: Option(str, description="Track name or URL")
    ) -> None:
        voice_state = ctx.author.voice
        if voice_state is None:
            await ctx.respond("You must be in a voice channel.")
            return

        await ctx.defer()

        if ctx.guild.id not in self.music_instances:
            vc = await voice_state.channel.connect()
            await ctx.guild.change_voice_state(channel=voice_state.channel, self_deaf=True)
            mi = MusicInstance(voice_client=vc)
            self.music_instances[ctx.guild.id] = mi
            mi.voice_client.play(FFmpegPCMAudio("../assets/audio/obi_wan_hello_there.mp3"))

        music_instance = self.music_instances[ctx.guild.id]

        if music_instance.voice_client.channel != voice_state.channel:
            await music_instance.voice_client.move_to(voice_state.channel)

        try:
            tracks = await _YouTube.search(query)
        except Exception as e:
            await ctx.respond(f"Error fetching audio: {e}")
            return

        music_instance.music_queue.extend(tracks)
        for title, *_ in tracks:
            await ctx.followup.send(f"Added {title} to the queue")

        if music_instance.active_music is None:
            await self.play_next(ctx.guild.id)

    @slash_command(description="Skip the current track | <amount>")
    async def skip(
        self,
        ctx: ApplicationContext,
        amount: Option(int, description="Number of tracks to skip") = 1
    ) -> None:
        if ctx.guild.id not in self.music_instances:
            await ctx.respond("Nothing is playing.")
            return

        music_instance = self.music_instances[ctx.guild.id]
        skip_count = max(min(amount - 1, len(music_instance.music_queue)), 0)
        for _ in range(skip_count):
            music_instance.music_queue.popleft()

        music_instance.voice_client.stop()
        await ctx.respond(f"Skipped {amount} track(s).")

    @slash_command(description="Stop playing and clear queue")
    async def stop(
        self,
        ctx: ApplicationContext
    ) -> None:
        if ctx.guild.id not in self.music_instances:
            await ctx.respond("Nothing is playing.")
            return

        music_instance = self.music_instances[ctx.guild.id]
        music_instance.music_queue.clear()
        music_instance.voice_client.stop()
        await ctx.respond("Stopped music and cleared the queue.")

    @slash_command(description="Pause the music")
    async def pause(
        self,
        ctx: ApplicationContext
    ) -> None:
        if ctx.guild.id not in self.music_instances:
            await ctx.respond("Nothing is playing.")
            return

        self.music_instances[ctx.guild.id].voice_client.pause()
        await ctx.respond("Music paused.")

    @slash_command(description="Resume the music")
    async def unpause(
        self,
        ctx: ApplicationContext
    ) -> None:
        if ctx.guild.id not in self.music_instances:
            await ctx.respond("Nothing is playing.")
            return

        self.music_instances[ctx.guild.id].voice_client.resume()
        await ctx.respond("Music resumed.")

    @slash_command(description="Show the current music queue")
    async def queue(
        self,
        ctx: ApplicationContext
    ) -> None:
        if ctx.guild.id not in self.music_instances:
            await ctx.respond("No music queue for this server.")
            return

        music_instance = self.music_instances[ctx.guild.id]

        if music_instance.active_music is None:
            await ctx.respond("The music queue is empty.")
            return

        output = [f"Now Playing: {music_instance.active_music}"]
        output.extend(f"{i+1}. {title}" for i, (title, _) in enumerate(music_instance.music_queue))

        output_str = "\n".join(output)
        await ctx.respond(output_str[:2000])

    @slash_command(description="Clear the music queue")
    async def clear(
        self,
        ctx: ApplicationContext
    ) -> None:
        if ctx.guild.id not in self.music_instances:
            await ctx.respond("No active queue to clear.")
            return

        self.music_instances[ctx.guild.id].music_queue.clear()
        await ctx.respond("Cleared the queue.")

    @slash_command(description="Remove a track from the queue | <queue position>")
    async def remove(
        self,
        ctx: ApplicationContext,
        queue_position: int
    ) -> None:
        if ctx.guild.id not in self.music_instances:
            await ctx.respond("No active queue to modify.")
            return

        music_instance = self.music_instances[ctx.guild.id]

        index = queue_position - 1
        if not (0 <= index < len(music_instance.music_queue)):
            await ctx.respond(f"Invalid position. Must be between 1 and {len(music_instance.music_queue)}")
            return

        title, _ = music_instance.music_queue[index]
        del music_instance.music_queue[index]
        await ctx.respond(f"Removed {title} from the queue.")

    @slash_command(description="Search for a track on YouTube | <track name or URL>")
    async def search(
        self,
        ctx: ApplicationContext, 
        query: Option(str, description="Track name or URL")
    ) -> None:
        await ctx.defer()
        try:
            tracks = await _YouTube.search(query)
        except Exception as e:
            await ctx.respond(f"Error searching YouTube: {e}")
            return

        output = "\n".join(f"{title}: {url}" for title, url in tracks)
        await ctx.followup.send(output[:2000])


def setup(bot: Bot):
    bot.add_cog(Music(bot))

