#!/usr/bin/env python3
import discord
import asyncio

name = 'thief'

def cat(path):
    with open(path, 'r') as f:
        text = f.read()
    return text

pawn = discord.Client()

@pawn.event
async def on_ready():
    u = pawn.user
    with open('var/bot/{}.id'.format(name), 'w') as f:
        f.write(str(u.id))
    with open('var/bot/{}.name'.format(name), 'w') as f:
        f.write(str(u.name + '#' + u.discriminator))

async def speak():
    await pawn.wait_until_ready()
    async def onspeak(rd, wr):
        known_ident_len = int(cat('etc/identlen'))
        try:
            while True:
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
                channel = pawn.get_channel(int(dest))
                if channel == None:
                    errmsg = "Invalid channel ID \"{}\" (parsed as {})".format(dest, int(dest))
                    with open('var/{}-error.log'.format(name), 'a') as f:
                        f.write(str(errmsg) + '\n')
                    raise errmsg
                await channel.send(msg)
        except asyncio.exceptions.IncompleteReadError:
            pass
        wr.close()
        await wr.wait_closed()
    server = await asyncio.start_server(
        onspeak, cat('etc/bot/{}.addr'.format(name)), int(cat('etc/bot/{}.port'.format(name)))
    )
    while not pawn.is_closed():
        async with server:
            await server.serve_forever()

# Start
pawn.loop.create_task(speak())
pawn.run(cat('etc/bot/{}.token'.format(name)))


