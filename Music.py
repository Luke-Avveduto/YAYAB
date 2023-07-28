import asyncio

from discord.ext import commands

from YTDLSource import YTDLSource

from playlists import get_playlist_urls, is_playlist

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.q = asyncio.Queue()
        self.blocker = asyncio.Event()

        self.volume = 10

        self.playing = False
        self.player = None

        self.paused = asyncio.Event()
        self.paused.set()

        bot.loop.create_task(self.player_loop())

        #This will be non-None when anything checks it because of the pre-command checks
        self.ctx = None

    def after_player_stop(self, e):
        self.playing = False
        self.bot.loop.call_soon_threadsafe(self.blocker.set)


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
            self.ctx.voice_client.play(self.player, after=self.after_player_stop)
            
            self.playing = True

            #Fix volume
            self.ctx.voice_client.source.volume = self.volume / 100

            await self.ctx.channel.send(f'Now playing: {self.player.title}')

            #Now we hold until the song is done by waiting on our blocker
            await self.blocker.wait()


            print("Song Finished Now")

    @commands.has_permissions(administrator=True)
    @commands.hybrid_command()
    async def play(self, ctx, *, url):
        """Takes a link to either a song or playlist and enqueues all the songs for playing"""

        if not self.playing:
            print("Nothing is playing right now")
            await ctx.send(delete_after=1, content="Playback will begin shortly", ephemeral=True)
        else:
            print("Something is playing right now")
            await ctx.send("Adding song(s) to the queue")
        
        #Load the song or playlists songs into the q
        if is_playlist(url):
            for vid in get_playlist_urls(url):
                print(vid)
                await self.q.put(vid)
        else:
            print(url)
            await self.q.put(url)

        

    @commands.has_permissions(administrator=True)              
    @commands.hybrid_command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

        #Update volume so next song will also use it
        self.volume = volume

    @commands.has_permissions(administrator=True)
    @commands.hybrid_command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.reply("Playback Stopped")

        #Reset our q
        self.q = asyncio.Queue()

        #Kill current player, this also unblocks since the after function is still run 
        self.player.cleanup()

        await ctx.voice_client.disconnect()

    @commands.has_permissions(administrator=True)
    @commands.hybrid_command()
    async def skip(self, ctx):
        """Skips the currently playing song"""

        await ctx.reply(f'Skipped Song: {self.player.title}')

        # Set the volume to 0 to avoid playing any corruption
        self.ctx.voice_client.source.volume = 0
        
        self.player.cleanup()


    @play.before_invoke
    @skip.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                self.ctx = ctx
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")