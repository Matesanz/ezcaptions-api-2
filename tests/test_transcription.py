import pytest
from unittest.mock import MagicMock, patch

from app.transcription import transcribe


def make_word(text, start, end):
    w = MagicMock()
    w.text = text
    w.start = start
    w.end = end
    return w


def mock_aai(words=None, error=None):
    """Return patched aai and get_settings mocks for use in tests."""
    transcript = MagicMock()
    transcript.error = error
    transcript.words = words

    mock = MagicMock()
    mock.Transcriber.return_value.transcribe.return_value = transcript
    return mock


# --- transcribe() ---

def test_transcribe_maps_words_to_captions():
    words = [make_word("Hello", 0, 500), make_word("world", 600, 1000)]

    with patch("app.transcription.get_settings") as mock_gs, \
         patch("app.transcription.aai", mock_aai(words=words)):
        mock_gs.return_value.assemblyai_key = "test-key"
        result = transcribe("https://example.com/video.mp4", "My Video")

    assert result.info.Title == "My Video"
    assert len(result.events) == 1
    assert len(result.events[0].Words) == 2
    assert result.events[0].Words[0].text == "Hello"
    assert result.events[0].Words[0].start == 0
    assert result.events[0].Words[0].end == 500
    assert result.events[0].Words[1].text == "world"


def test_transcribe_uses_default_title():
    with patch("app.transcription.get_settings") as mock_gs, \
         patch("app.transcription.aai", mock_aai(words=[])):
        mock_gs.return_value.assemblyai_key = "test-key"
        result = transcribe("https://example.com/video.mp4")

    assert result.info.Title == "Default Title"


def test_transcribe_empty_words():
    with patch("app.transcription.get_settings") as mock_gs, \
         patch("app.transcription.aai", mock_aai(words=[])):
        mock_gs.return_value.assemblyai_key = "test-key"
        result = transcribe("https://example.com/video.mp4")

    assert result.events[0].Words == []


def test_transcribe_none_words_treated_as_empty():
    with patch("app.transcription.get_settings") as mock_gs, \
         patch("app.transcription.aai", mock_aai(words=None)):
        mock_gs.return_value.assemblyai_key = "test-key"
        result = transcribe("https://example.com/video.mp4")

    assert result.events[0].Words == []


def test_transcribe_raises_on_error():
    with patch("app.transcription.get_settings") as mock_gs, \
         patch("app.transcription.aai", mock_aai(error="Audio file not found")):
        mock_gs.return_value.assemblyai_key = "test-key"
        with pytest.raises(RuntimeError, match="Audio file not found"):
            transcribe("https://example.com/bad.mp4")


def test_transcribe_sets_api_key():
    mock = mock_aai(words=[])
    with patch("app.transcription.get_settings") as mock_gs, \
         patch("app.transcription.aai", mock):
        mock_gs.return_value.assemblyai_key = "my-secret-key"
        transcribe("https://example.com/video.mp4")

    assert mock.settings.api_key == "my-secret-key"


def test_transcribe_language_detection_when_no_language():
    mock = mock_aai(words=[])
    with patch("app.transcription.get_settings") as mock_gs, \
         patch("app.transcription.aai", mock):
        mock_gs.return_value.assemblyai_key = "test-key"
        transcribe("https://example.com/video.mp4")

    mock.TranscriptionConfig.assert_called_once_with(
        language_code=None,
        language_detection=True,
        speech_model=mock.SpeechModel["best"],
    )


def test_transcribe_language_code_disables_detection():
    mock = mock_aai(words=[])
    with patch("app.transcription.get_settings") as mock_gs, \
         patch("app.transcription.aai", mock):
        mock_gs.return_value.assemblyai_key = "test-key"
        transcribe("https://example.com/video.mp4", language="fr")

    mock.TranscriptionConfig.assert_called_once_with(
        language_code="fr",
        language_detection=False,
        speech_model=mock.SpeechModel["best"],
    )


def test_transcribe_passes_speech_model():
    mock = mock_aai(words=[])
    with patch("app.transcription.get_settings") as mock_gs, \
         patch("app.transcription.aai", mock):
        mock_gs.return_value.assemblyai_key = "test-key"
        transcribe("https://example.com/video.mp4", speech_model="nano")

    mock.TranscriptionConfig.assert_called_once_with(
        language_code=None,
        language_detection=True,
        speech_model=mock.SpeechModel["nano"],
    )
