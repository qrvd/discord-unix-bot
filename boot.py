#!/usr/bin/env python3
import asyncio
import discord
import sys

LOGFILE = 'var/log/kanna-error'

def cat(path):
    with open(path, 'r') as f:
        text = f.read()
    return text

def print0(*words):
    for w in words:
        print(w, end="\0")
    sys.stdout.flush()

kanna = discord.Client()

@kanna.event
async def on_ready():
    u = kanna.user
    print0(u.id, u.name + '#' + u.discriminator)

@kanna.event
async def on_message(m):
    a = m.author
    c = m.channel
    t = type(c)
    tn = a.name + '#' + a.discriminator
    if t == discord.channel.TextChannel:
        print0(c.id, '#' + c.name, a.id, tn, m.content)
    elif t == discord.channel.DMChannel:
        print0(c.id, '@' + tn, a.id, tn, m.content)
    else:
        raise ("Unknown prefix for stream {}".format(c.id), c)

async def speak():
    await kanna.wait_until_ready()
    async def onspeak(rd, wr):
        known_ident_len = int(cat('etc/identlen'))
        try:
            while True:
                action = (await rd.readuntil(separator=b'\0'))[:-1].decode()
                if action == 'say':
                    dest = (await rd.readuntil(separator=b'\0'))[:-1].decode()
                    if len(dest) != known_ident_len:
                        with open('fail', 'a') as f:
                            f.write("ID string of wrong size (expected {}, got {})\n".format(known_ident_len, dest))
                        raise ("ID string of wrong size (expected {})".format(known_ident_len), dest)
                    lenstr = (await rd.readuntil(separator=b'\0'))[:-1].decode()
                    msglen = int(lenstr)
                    if msglen <= 0:
                        raise ("Invalid message length", lenstr, msglen)
                    elif msglen > 2000:
                        raise ("Message too long", lenstr, msglen)
                    msg = (await rd.readexactly(msglen - 1)).decode()
                    if len(msg) == 0:
                        raise "Can't send an empty message"
                    channel = kanna.get_channel(int(dest))
                    if channel == None:
                        errmsg = "Invalid channel ID \"{}\" (parsed as {})".format(dest, int(dest))
                        with open(LOGFILE, 'a') as f:
                            f.write(str(errmsg) + '\n')
                        raise errmsg
                    m = await channel.send(msg)
                    with open('var/say.last-message-id', 'w') as f:
                        f.write(str(m.id))
                elif action == 'delete':
                    channel_id = (await rd.readuntil(separator=b'\0'))[:-1].decode()
                    msg_id = (await rd.readuntil(separator=b'\0'))[:-1].decode()
                    channel = kanna.get_channel(int(channel_id))
                    if channel == None:
                        with open(LOGFILE, 'a') as f:
                            f.write("delete: invalid channel id {}\n".format(channel_id))
                        continue
                    msg = await channel.fetch_message(int(msg_id))
                    if msg == None:
                        with open(LOGFILE, 'a') as f:
                            f.write("delete: invalid message id {} in channel {}\n".format(msg_id, channel_id))
                        continue
                    await msg.delete()
        except asyncio.exceptions.IncompleteReadError:
            pass
        wr.close()
        await wr.wait_closed()
    server = await asyncio.start_server(
        onspeak, cat('etc/speakaddr'), int(cat('etc/speakport'))
    )
    while not kanna.is_closed():
        async with server:
            await server.serve_forever()

# Start!
kanna.loop.create_task(speak())
kanna.run(cat('etc/token/kanna'))

