import asyncio
from collections import deque
import logging
import os
from pathlib import Path
from queue import Queue
import random
import re
from threading import Thread
from typing import Callable, Generator, Iterable

from discord import ApplicationContext, Bot, Cog, FFmpegPCMAudio, Option, VoiceClient, slash_command
from discord.channel import VocalGuildChannel
from dotenv import load_dotenv
import spotipy
from spotipy import SpotifyClientCredentials
from yt_dlp import YoutubeDL


class Spotify:
    TRACK_URL_REGEX = re.compile(r"(https?://)?(www\.)?open\.spotify\.com/track/([a-zA-Z0-9]+)")
    PLAYLIST_URL_REGEX = re.compile(r"(https?://)?(www\.)?open\.spotify\.com/playlist/([a-zA-Z0-9]+)")
    ALBUM_URL_REGEX = re.compile(r"(https?://)?(www\.)?open\.spotify\.com/album/([a-zA-Z0-9]+)")
    ARTIST_URL_REGEX = re.compile(r"(https?://)?(www\.)?open\.spotify\.com/artist/([a-zA-Z0-9]+)")
    
    load_dotenv()
    _sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials()
    )
    
    @staticmethod
    def _track_to_title(track: dict) -> str:
        artist = track["artists"][0]["name"]
        name = track["name"]

        return f"{artist} - {name}"

    @classmethod
    def track_to_title(cls, track_id: str) -> str:
        track = cls._sp.track(track_id)
        if track == None:
            raise ValueError("Invalid track id")

        return Spotify._track_to_title(track)

    @classmethod
    def playlist_to_titles(cls, playlist_id: str) -> tuple[str, ...]:
        playlist = cls._sp.playlist_tracks(playlist_id)
        if playlist is None:
            raise ValueError("Invalid playlist id")
        
        return tuple(Spotify._track_to_title(item["track"]) for item in playlist["items"])

    @classmethod
    def album_to_titles(cls, album_id: str) -> tuple[str, ...]:
        album = cls._sp.album_tracks(album_id)
        if album is None:
            raise ValueError("Invalid album id")
        
        return tuple(Spotify._track_to_title(track) for track in album["items"])

    @classmethod
    def artist_to_titles(cls, artist_id: str) -> tuple[str, ...]:
        album = cls._sp.artist_top_tracks(artist_id)
        if album is None:
            raise ValueError("Invalid artist id")
        
        return tuple(Spotify._track_to_title(track) for track in album["tracks"])


class Youtube:
    VIDEO_URL_REGEX = re.compile(r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube-nocookie\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})")
    PLAYLIST_URL_REGEX = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtube-nocookie\.com)/.*[?&]list=([a-zA-Z0-9_-]+)")

    COMMON_OPTIONS = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True
    }
    SEARCH_OPTIONS = COMMON_OPTIONS | {
        "skip_download": True,
        "flat_playlist": True,
        "extract_flat": "in_playlist",
    }
    DOWNLOAD_OPTIONS = COMMON_OPTIONS | {
        "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio",
        "extractaudio": True,
        "concurrent_fragments": 5,
        "buffer_size": "16K",
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 3,
        "outtmpl": "%(title)s [%(id)s].%(ext)s"
    }

    @classmethod
    def fast_search(cls, url: str) -> Generator[str, None, None]:
        with YoutubeDL(cls.SEARCH_OPTIONS) as ydl:
            result = ydl.extract_info(url, download=False)
            if result is None or "entries" not in result or not result["entries"]:
                raise ValueError("Invalid URL, no results were found")
            
            return (entry["id"] for entry in result["entries"])

    @classmethod
    def download(cls, video_ids: Iterable[str], download_dir: Path) -> None:
        with YoutubeDL(cls.DOWNLOAD_OPTIONS | {"paths": {"home": str(download_dir)}}) as ydl:
            urls = [f"https://www.youtube.com/watch?v={video_id}" for video_id in video_ids]
            ydl.download(urls)


class FileCache:
    CACHE_DIR = Path("./audio_cache")
    CACHE_MAX_SIZE = 8 * 1024 ** 3

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def _get_files(cls, pattern: str = "*") -> tuple[Path, ...]:
        return tuple(file for file in cls.CACHE_DIR.rglob(pattern) if file.is_file())
    
    @classmethod
    def _get_total_cache_size(cls) -> int:
        return sum(file.stat().st_size for file in cls._get_files())

    @classmethod
    def _should_evict(cls) -> bool:
        return cls._get_total_cache_size() > cls.CACHE_MAX_SIZE

    @classmethod
    def _get_least_recently_used_file(cls) -> Path:
        files = cls._get_files()
        if not files:
            raise FileNotFoundError("No files in cache")

        return min(files, key=lambda f: f.stat().st_atime_ns)

    @classmethod
    def _evict_least_recently_used(cls) -> None:
        cls._get_least_recently_used_file().unlink()

    @classmethod
    def evict_cache(cls) -> None:
        while cls._should_evict():
            cls._evict_least_recently_used()

    @staticmethod
    def update_timestamp(file: Path) -> None:
        os.utime(file, None)

    @classmethod
    def get_file(cls, pattern: str) -> Path | None:
        file = next(cls.CACHE_DIR.rglob(pattern), None)
        if file is not None:
            cls.update_timestamp(file)
            return file


class AudioFetcher:
    @staticmethod
    def _search(query: str) -> Generator[str, None, None]:
        youtube_playlist = Youtube.PLAYLIST_URL_REGEX.match(query)
        youtube_video = Youtube.VIDEO_URL_REGEX.match(query)

        spotify_track = Spotify.TRACK_URL_REGEX.match(query)
        spotify_playlist = Spotify.PLAYLIST_URL_REGEX.match(query)
        spotify_album = Spotify.ALBUM_URL_REGEX.match(query)
        spotify_artist = Spotify.ARTIST_URL_REGEX.match(query)

        if youtube_playlist:
            return Youtube.fast_search(query)

        if youtube_video:
            return (id for id in (youtube_video[4],))

        if spotify_track:
            track_id = spotify_track[3]
            track_title = Spotify.track_to_title(track_id)
            url = "ytsearch1:" + track_title

            return Youtube.fast_search(url)

        if spotify_playlist:
            playlist_id = spotify_playlist[3]

            return (
                next(Youtube.fast_search("ytsearch1:" + title))
                for title in Spotify.playlist_to_titles(playlist_id)
            )

        if spotify_album:
            album_id = spotify_album[3]

            return (
                next(Youtube.fast_search("ytsearch1:" + title))
                for title in Spotify.album_to_titles(album_id)
            )

        if spotify_artist:
            artist_id = spotify_artist[3]

            return (
                next(Youtube.fast_search("ytsearch1:" + title))
                for title in Spotify.artist_to_titles(artist_id)
            )

        return Youtube.fast_search("ytsearch1:" + query)

    @staticmethod
    def get_files_and_titles(query: str) -> Generator[tuple[Path, str], None, None]:
        try:
            video_ids = AudioFetcher._search(query)
        except Exception as e:
            logging.warning(f"Search failed for {query}: {e}")
            return
        
        for video_id in video_ids:
            file_pattern = fr"*{video_id}*"
            file = FileCache.get_file(file_pattern)

            if file is None:
                Youtube.download((video_id,), FileCache.CACHE_DIR)
                FileCache.evict_cache()
                file = FileCache.get_file(file_pattern)

            if file is None:
                continue

            title = file.stem.rsplit(' ', maxsplit=1)[0]

            yield (file, title)


class PlaybackInstance:
    GREETING_AUDIO_PATH = Path("./assets/audio/obi_wan_hello_there.mp3")

    def __init__(self, voice_client: VoiceClient, on_finished: Callable[[], None] | None = None):
        self.voice_client = voice_client
        self.on_finished = on_finished
        self.audio_queue: deque[tuple[Path, str]] = deque()
        self.query_queue: Queue[str | None] = Queue()

        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("Expected an active event loop, but none is running.")

        self._query_worker_td = Thread(target=self._process_queries, daemon=True)
        self._query_worker_td.start()

    def _process_queries(self) -> None:
        while True:
            query = self.query_queue.get()
            if query is None:
                return

            for file_path, title in AudioFetcher.get_files_and_titles(query):
                asyncio.run_coroutine_threadsafe(
                    self._enqueue_audio(file_path, title),
                    self._loop
                )

    @property
    def currently_playing(self) -> tuple[Path, str] | None:
        return self.audio_queue[0] if self.audio_queue else None

    @property
    def coming_up(self) -> list[tuple[Path, str]]:
        return list(self.audio_queue)[1:]

    def _enqueue(self, query: str | None) ->  None:
        self.query_queue.put(query)

    def enqueue(self, query: str) ->  None:
        self._enqueue(query)

    async def play(self) -> None:
        if not self.audio_queue:
            await self.stop()
            return

        audio_file, _ = self.audio_queue[0]
        self.voice_client.play(
            FFmpegPCMAudio(str(audio_file)),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self._play_next(),
                self._loop
            ) if e is None else None
        )

    async def _play_next(self):
        self.audio_queue.popleft()
        await self.play()

    async def _enqueue_audio(self, file_path: Path, title: str) -> None:
        logging.debug(f"Queueing {title}")
        self.audio_queue.append((file_path, title))

        if not self.voice_client.is_playing():
            await self.play()

    def greet(self) -> None:
        self.voice_client.play(FFmpegPCMAudio(str(self.GREETING_AUDIO_PATH)))

    async def join_channel(
        self,
        channel: VocalGuildChannel
    ) -> None:
        await self.voice_client.move_to(channel)
        self.greet()

    def pause(self) -> None:
        self.voice_client.pause()

    def resume(self) -> None:
        self.voice_client.resume()

    def skip(self, amount: int) -> int:
        amount = min(max(0, amount), len(self.audio_queue))
        for _ in range(amount):
            self.audio_queue.popleft()
        
        self.voice_client.stop()
        return amount

    async def clear(self) -> None:
        self.audio_queue.clear()

        self.query_queue.empty()
        self._enqueue(None)
        await asyncio.to_thread(self._query_worker_td.join)


    async def stop(self) -> None:
        self.audio_queue.clear()

        self.query_queue.empty()
        self._enqueue(None)
        await asyncio.to_thread(self._query_worker_td.join)

        self.voice_client.stop()
        await self.voice_client.disconnect()
        
        if self.on_finished is not None:
            self.on_finished()

    # Datarace can occur here
    def shuffle(self) -> None:
        upcoming = self.coming_up
        if not upcoming:
            return

        current = self.currently_playing
        assert current is not None

        random.shuffle(upcoming)

        self.audio_queue.clear()
        self.audio_queue.append(current)
        self.audio_queue.extend(upcoming)


class Audio(Cog):
    def __init__(self, _bot: Bot):
        self._bot = _bot
        self._playback_instances: dict[int, PlaybackInstance] = {}

    def _delete_playback_instance(self, guild_id: int) -> None:
        if guild_id in self._playback_instances:
            del self._playback_instances[guild_id]

    @slash_command(description="Play audio | <track name or URL>")
    async def play(
        self,
        ctx: ApplicationContext,
        query: Option(str, description="Audio name or URL")
    ) -> None:
        user_voice_state = ctx.author.voice
        if user_voice_state is None:
            await ctx.respond("You must be in a voice channel")
            return

        if ctx.guild_id not in self._playback_instances:
            user_voice_channel = user_voice_state.channel
            assert user_voice_channel is not None

            playback_instance = self._playback_instances[ctx.guild_id] = PlaybackInstance(
                await user_voice_channel.connect(),
                lambda: self._delete_playback_instance(ctx.guild_id)
            )
            await playback_instance.join_channel(user_voice_channel)

        playback_instance = self._playback_instances[ctx.guild_id]

        playback_instance.enqueue(query)

        await ctx.respond("Added requested audio to queue")


    @slash_command(description="Skip the current track | <amount>")
    async def skip(
        self,
        ctx: ApplicationContext,
        amount: Option(int, description="Number of tracks to skip") = 1
    ) -> None:
        if ctx.guild_id not in self._playback_instances:
            await ctx.respond("Nothing is playing")
            return

        skipped_tracks = self._playback_instances[ctx.guild_id].skip(amount)

        await ctx.respond(f"Skipped {skipped_tracks} track{"s" if skipped_tracks != 1 else ""}")

    @slash_command(description="Stop playing and clear queue")
    async def stop(
        self,
        ctx: ApplicationContext
    ) -> None:
        if ctx.guild_id not in self._playback_instances:
            return

        await self._playback_instances[ctx.guild_id].stop()

    @slash_command(description="Pause the music")
    async def pause(
        self,
        ctx: ApplicationContext
    ) -> None:
        if ctx.guild_id not in self._playback_instances:
            return

        self._playback_instances[ctx.guild_id].pause()

    @slash_command(description="Resume the music")
    async def resume(
        self,
        ctx: ApplicationContext
    ) -> None:
        if ctx.guild_id not in self._playback_instances:
            return

        self._playback_instances[ctx.guild_id].resume()

    @slash_command(description="Show the current music queue")
    async def queue(
        self,
        ctx: ApplicationContext
    ) -> None:
        playback_instance = self._playback_instances.get(ctx.guild_id)
        if playback_instance is None:
            await ctx.respond("The queue is currently empty")
            return

        currently_playing = playback_instance.currently_playing[1]
        coming_up = playback_instance.coming_up
        
        output = [f"Now Playing: {currently_playing}"]
        output.extend(f"{i}. {title}" for i, (_, title) in enumerate(coming_up, 1))

        output_str = "\n".join(output)
        for i in range(0, len(output_str), 2000):
            await ctx.respond(output_str[i:i + 2000])

    @slash_command(description="Clear the audio queue")
    async def clear(
        self,
        ctx: ApplicationContext
    ) -> None:
        ctx.respond("This functionality is not yet implemented, use /stop + /play instead")

    @slash_command(description="Remove a track from the queue | <queue position>")
    async def remove(
        self,
        ctx: ApplicationContext,
        queue_position: int
    ) -> None:
        pass

    @slash_command(description="Shuffle the audio queue")
    async def shuffle(
        self,
        ctx: ApplicationContext
    ) -> None:
        playback_instance = self._playback_instances.get(ctx.guild_id)
        if playback_instance is not None:
            playback_instance.shuffle()

        ctx.respond("Shuffling queue")

def setup(bot: Bot):
    bot.add_cog(Audio(bot))

