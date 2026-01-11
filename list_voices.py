import asyncio
import edge_tts

async def list_voices():
    voices = await edge_tts.list_voices()
    indian_voices = [v for v in voices if v['Locale'].startswith('hi-IN')]
    print("Available Indian voices:")
    for v in indian_voices:
        print(f"- {v['ShortName']}: {v['Gender']} - {v['VoiceTag']['VoicePersonalities']}")

asyncio.run(list_voices())