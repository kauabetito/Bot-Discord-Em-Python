import discord
import yt_dlp
import asyncio
from discord.ext import commands
from decouple import config

# Configuração dos intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Inicializando o bot
client = commands.Bot(command_prefix="!", intents=intents)

# Altere para o caminho onde o FFmpeg está instalado
FFMPEG_PATH = "C:\\Users\\kaual\\OneDrive\\Área de Trabalho\\ffmpeg-2024-06-13-git-0060a368b1-full_build\\bin\\ffmpeg.exe"
FFMPEG_OPTIONS = {'options': '-vn', 'executable': FFMPEG_PATH}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}


class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("Você precisa estar em um canal de voz primeiro!")

        if not ctx.voice_client:
            await voice_channel.connect()
        elif ctx.voice_client.channel != voice_channel:
            await ctx.voice_client.move_to(voice_channel)

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                try:
                    info = ydl.extract_info(
                        f"ytsearch:{search}", download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    url = info['url']
                    title = info['title']
                    self.queue.append((url, title))
                    await ctx.send(f'Adicionado à fila: **{title}**')
                except Exception as e:
                    await ctx.send("Não consegui baixar a música. Erro: " + str(e))
                    return

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        if self.queue:
            url, title = self.queue.pop(0)
            try:
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                ctx.voice_client.play(
                    source, after=lambda e: self.client.loop.create_task(
                        self.play_next(ctx))
                )
                await ctx.send(f'Tocando agora: **{title}**')
            except Exception as e:
                await ctx.send("Ocorreu um erro ao tentar tocar a música: " + str(e))
                if not ctx.voice_client.is_playing():
                    await ctx.send("A fila está vazia!")
        else:
            await ctx.send("A fila está vazia!")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Música pulada ⏭")
        else:
            await ctx.send("Não estou tocando nada no momento.")

# Evento para quando o bot estiver pronto


@client.event
async def on_ready():
    print(f"Conectado como {client.user}")

# Evento para processar mensagens e comandos


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Palavras ofensivas a serem monitoradas
    palavras_ofensivas = ["Filho da puta", "cu", "cachorra",
                          "desgraçado", "trouxa", "idiota", "viadinho"]
    if any(palavra in message.content for palavra in palavras_ofensivas):
        await message.channel.send(f"Por favor, {message.author.name}, não ofenda os demais usuários.")
        await message.delete()

    await client.process_commands(message)


@client.command(name="oi")
async def send_hello(ctx):
    name = ctx.author.name
    response = "Olá, " + name
    await ctx.send(response)


# Comando para o bot entrar no canal de voz
@client.command()
async def entrar(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
        canal = ctx.author.voice.channel
        await canal.connect()
    else:
        await ctx.send("Você precisa estar em um canal de voz primeiro.")


# Adiciona a classe MusicBot ao bot e inicia o bot com o token
async def main():
    await client.add_cog(MusicBot(client))
    token = config("TOKEN")
    await client.start(token)

# Executa o bot
asyncio.run(main())
