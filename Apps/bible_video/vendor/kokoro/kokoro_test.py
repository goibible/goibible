from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code="a")

generator = pipeline(
    "This is a Kokoro test.",
    voice="af_nova"
)

for i, (_, _, audio) in enumerate(generator):
    sf.write(f"test_{i}.wav", audio, 24000)
