import assemblyai as aai

from .config import get_settings
from .models import Captions, CaptionsEvent, CaptionsInfo, CaptionsWord


def transcribe(
    url: str,
    title: str = "Default Title",
    language: str | None = None,
    speech_model: str = "best",
) -> Captions:
    aai.settings.api_key = get_settings().assemblyai_key

    config = aai.TranscriptionConfig(
        language_code=language,
        language_detection=language is None,
        speech_model=aai.SpeechModel[speech_model],
    )

    transcript = aai.Transcriber().transcribe(url, config=config)

    if transcript.error:
        raise RuntimeError(transcript.error)

    words = [
        CaptionsWord(text=w.text, start=w.start, end=w.end)
        for w in (transcript.words or [])
    ]

    return Captions(
        info=CaptionsInfo(Title=title),
        events=[CaptionsEvent(Words=words)],
    )
