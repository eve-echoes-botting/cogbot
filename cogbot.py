import asyncio
import discord
from discord.ext import commands, tasks
from cogwatch import Watcher
import logging
from logging.handlers import QueueHandler
import queue
import sys
from io import TextIOBase


DEFAULT_CHANNEL = 987755418744930394
id4o = 139179662369751041

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

with open('token') as f:
    token = f.read()

class bot4o(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix = '.', intents = intents)
        self.q = queue.Queue()
        self.renameq = queue.Queue()
        self.id4o = id4o

    def stdout(self, msg):
        self.q.put(msg)

    @tasks.loop(minutes = 6)
    async def renameloop(self):
        if self.renameq.qsize() > 0:
            t = self.renameq.get(block = False)
            await self._rename(t)

    @tasks.loop(seconds = 2)
    async def msgloop(self):
        try:
            msg = ''
            if self.q.qsize() > 0:
                item = self.q.get(block = False)
            while isinstance(item, str):
                msg += item
                if self.q.qsize() > 0:
                    item = self.q.get(block = False)
                else:
                    item = None
            if len(msg) > 0:
                await self._send('```\n' + msg + '```')
            if isinstance(item, tuple):
                try:
                    await self._send(item[1], item[2], **item[0])
                    return
                except:
                    pass
        except:
            pass

    async def on_ready(self):
        self.w = Watcher(self, path = 'commands', preload = True)
        await self.w.start()
        self.msgloop.start()
        self.renameloop.start()
        await self.send(self.get_channel(int(DEFAULT_CHANNEL)), 'im up')
        await self.change_presence(activity=discord.Game(name="your string goes here"))

    async def on_message(self, message):
        if message.author.bot:
            return
        try:
            await self.process_commands(message)
        except Exception as e:
            await self.send(message.channel, str(e))
            raise

    async def on_message_error(self, ctx, error):
        await self.send(ctx, 'cogbot error: ' + str(error))

    async def send(self, ctx, msg  = None, **args):
        self.q.put((args, ctx, msg))
        
    async def _send(self, ctx, msg  = None, **args):
        c = ctx
        if isinstance(ctx, int):
            ctx = self.get_channel(ctx)
            if ctx == None:
                ctx = self.get_user(c)
        if msg == None:
            msg = ctx
            ctx = None
        if ctx == None:
            ctx = self.get_channel(int(DEFAULT_CHANNEL))
        if isinstance(msg, list):
            for i in msg:
                await self.send(ctx, i, **args)
        elif isinstance(msg, str):
            if ctx == None:
                print(f'failed to get channel from {c}')
            else:
                return await ctx.send(msg, **args)
        else:
            raise Exception('invalid msg type')

    async def rename(self, c, n):
        self.renameq.put((c, n))

    async def _rename(self, r):
        c = r[0]
        n = r[1]
        if isinstance(c, int):
            c = self.get_channel(c)
        await c.edit(name = n)

b = bot4o()
@b.command()
async def stdo(ctx):
    await b.send('sending something to stdo')
    print('something')

@b.command()
async def reload(ctx):
    await b.w._preload()

@b.command()
async def hello(ctx):
    await ctx.send("hi, i'm the new bot")

@b.command()
async def close(ctx):
    if ctx.author.id == id4o:
        await b.send(ctx, 'im going down')
        await b.close()

sys.stderr.write = b.stdout
sys.stdout.write = b.stdout

b.run(token)
