import asyncio

from discord.ext import commands

from YTDLSource import YTDLSource

from playlists import get_playlist_urls, is_playlist

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.q = asyncio.Queue()
        self.blocker = asyncio.Event()

        self.default_volume = 10

        self.player = None

        self.paused = asyncio.Event()
        self.paused.set()

        bot.loop.create_task(self.player_loop())

        #Thiswill be non-None when anything checks it because of the pre-command checks
        self.ctx = None


    #The bot always trying to play music in the queue
    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            
            print("Blocker enabled")
            #Set the blocker to hold mode
            self.blocker.clear()

            print("Waiting for the next song in the q")
            #Wait for the next song to be enqueued
            url = await self.q.get()

            print("Got song: " + url)
            #Download and play the song
            #The actual playing of the song is handled by discord and is done in seperate thread, the await is misleading
            self.player = await YTDLSource.from_url(url, loop=self.bot.loop, stream = True)
            
            #Once the song is done, our blocker will unblock and we will we will loop
            self.ctx.voice_client.play(self.player, after=lambda _: self.bot.loop.call_soon_threadsafe(self.blocker.set))
            
            #Fix volume
            self.ctx.voice_client.source.volume = self.default_volume / 100

            await self.ctx.send(f'Now playing: {self.player.title}')

            #Now we hold until the song is done by waiting on our blocker
            await self.blocker.wait()


            print("Song Finished Now")


    @commands.command()
    async def play(self, ctx, *, url):
        """Takes a link to either a song or playlist and enqueues all the songs for playing"""

        #Load the song or playlists songs into the q
        if is_playlist(url):
            for vid in get_playlist_urls(url):
                await self.q.put(vid)
        else:
            await self.q.put(url)

        #Disable the paused blocker
        self.paused.set()
                    

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        #Reset our q
        self.q = asyncio.Queue()

        #Kill current player, this also unblocks since the after function is still run 
        self.player.cleanup()

        await ctx.voice_client.disconnect()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                self.ctx = ctx
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()