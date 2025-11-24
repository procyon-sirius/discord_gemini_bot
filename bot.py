import discord
from discord.ext import commands
from google import genai
import os
import asyncio

# ⚠️ 환경 변수에서 키를 불러옵니다.
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 1. Gemini 클라이언트 초기화
# 환경 변수가 설정되지 않았을 경우 오류 발생
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

try:
    client_ai = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Gemini 클라이언트 초기화 오류: API 키가 올바른 형식인지 확인하세요. {e}")
    exit()

# 모델 선택
GEMINI_MODEL = 'gemini-2.5-pro'

# 2. 디스코드 봇 클라이언트 초기화
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """봇이 성공적으로 로그인했을 때 호출됩니다."""
    print(f'로그인 성공: {bot.user.name} (ID: {bot.user.id})')
    # 봇이 서버에 연결된 후, 슬래시 명령어를 동기화합니다.
    try:
        # 전역 명령어 동기화
        synced = await bot.tree.sync()
        print(f"동기화된 슬래시 명령어: {len(synced)}개")
    except Exception as e:
        print(f"슬래시 명령어 동기화 중 오류 발생: {e}")


# 3. 슬래시 명령어 정의 (/gemini)
@bot.tree.command(name="gemini", description="Gemini AI에게 질문하고 답변을 받습니다.")
@discord.app_commands.describe(
    질문="Gemini에게 할 질문을 입력해주세요."
)
async def gemini_command(interaction: discord.Interaction, 질문: str):
    """
    디스코드의 슬래시 명령어 (/gemini)를 처리하고 Embed 형태로 응답합니다.
    (사용자의 질문 내용을 포함하도록 수정되었습니다.)
    """
    # 응답 대기 메시지를 먼저 보냅니다.
    await interaction.response.defer(thinking=True)
    
    # Gemini 모델에 전달할 프롬프트 구성
    prompt = f"[Discord User: {interaction.user.name}] Question: {질문}"

    try:
        # 4. Gemini API 호출
        response = client_ai.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        response_text = response.text
        
        # 5. Embed 생성 및 응답 전송 (질문 포함)
        
        # Embed 생성
        embed = discord.Embed(
            title="✨ Gemini AI 답변",
            description=f"**질문자:** {interaction.user.mention}", # 질문자 멘션
            color=0x42f5e7 
        )
        
        # 질문 내용 필드 추가
        embed.add_field(
            name="📝 당신의 질문", 
            value=f"```\n{질문}\n```", # 코드 블록으로 감싸 깔끔하게 표시
            inline=False
        )
        
        # 답변 내용 필드 추가 및 1024자 제한 처리
        if len(response_text) > 1024:
            embed.add_field(
                name="💡 Gemini 답변 (일부)", 
                value=response_text[:1020] + "...", 
                inline=False
            )
        else:
            embed.add_field(
                name="💡 Gemini 답변", 
                value=response_text, 
                inline=False
            )

        embed.set_footer(text=f"Model: {GEMINI_MODEL}")
        
        # 최종 응답 전송
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {e}")
        await interaction.followup.send(
            "죄송합니다, AI 응답 처리 중 오류가 발생했습니다. (서버 문제 또는 API 키 확인)", 
            ephemeral=True
        )


# 6. 봇 실행
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN 환경 변수를 설정해야 합니다.")

try:
    bot.run(DISCORD_TOKEN)
except discord.HTTPException as e:
    if e.code == 4014:
        print("ERROR: Invalid Intents! Discord Developer Portal에서 Message Content Intent를 활성화했는지 확인하세요.")
    elif e.code == 4001:
        print("ERROR: 토큰이 유효하지 않습니다. DISCORD_BOT_TOKEN 환경 변수의 값을 다시 확인해주세요.")
    else:
        print(f"봇 실행 중 HTTP 오류 발생: {e}")
except Exception as e:
    print(f"봇 실행 중 오류 발생: {e}")