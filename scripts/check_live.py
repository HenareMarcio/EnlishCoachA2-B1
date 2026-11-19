import asyncio
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-3.8-live").strip()
CONFIG = {
    "response_modalities": ["AUDIO"],
    "output_audio_transcription": {},
}
VERSIONS = [None, "v1beta", "v1alpha"]


def make_client(version):
    options = types.HttpOptions(api_version=version) if version else None
    return genai.Client(api_key=API_KEY, http_options=options)


def list_live_models():
    print("Modelos de voz que a sua chave enxerga:")
    found = False
    try:
        for m in make_client(None).models.list():
            acts = m.supported_actions or []
            if "bidiGenerateContent" in acts or "live" in m.name:
                print("  ", m.name)
                found = True
    except Exception as exc:
        print("   (nao foi possivel listar:", exc, ")")
        return
    if not found:
        print("   (nenhum modelo de voz listado)")
    print()


async def try_version(version):
    client = make_client(version)
    async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
        await session.send_realtime_input(
            text="Hello! Please say hi in one short, friendly sentence."
        )
        audio_bytes = 0
        print("   Coach: ", end="", flush=True)
        async for response in session.receive():
            content = response.server_content
            if not content:
                continue
            if content.model_turn:
                for part in content.model_turn.parts or []:
                    if part.inline_data and part.inline_data.data:
                        audio_bytes += len(part.inline_data.data)
            if content.output_transcription and content.output_transcription.text:
                print(content.output_transcription.text, end="", flush=True)
            if content.turn_complete:
                break
        print()
        return audio_bytes


async def main():
    if not API_KEY or API_KEY.upper().startswith("SUA_"):
        print("ERRO: GEMINI_API_KEY ausente ou com valor de exemplo no .env.")
        return 1

    print(f"Modelo de voz: {MODEL}\n")
    list_live_models()

    for version in VERSIONS:
        label = version or "padrao do SDK"
        print(f"Tentando api_version = {label} ...")
        try:
            audio_bytes = await try_version(version)
        except Exception as exc:
            print(f"   falhou: {exc}\n")
            continue
        print(f"   audio recebido: {audio_bytes} bytes")
        if audio_bytes:
            print(f"\nOK: funcionou com api_version = {label}")
            return 0
        print("   conectou, mas nao veio audio.\n")

    print("Nenhuma versao funcionou. Me envie esta saida completa.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
