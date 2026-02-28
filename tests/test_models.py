from app.models import _format_ass_time, CaptionsWord, CaptionsEvent, Captions


def word(text: str, start: int, end: int) -> CaptionsWord:
    return CaptionsWord(text=text, start=start, end=end)


# --- _format_ass_time ---

def test_format_ass_time_zero():
    assert _format_ass_time(0) == "0:00:00.00"


def test_format_ass_time_seconds():
    assert _format_ass_time(3500) == "0:00:03.50"


def test_format_ass_time_full():
    ms = 1 * 3600000 + 2 * 60000 + 3 * 1000 + 400
    assert _format_ass_time(ms) == "1:02:03.40"


# --- CaptionsEvent ---

def test_event_full_text():
    event = CaptionsEvent(Words=[word("Hello", 0, 500), word("world", 500, 1000)])
    assert event.full_text == "Hello world"


def test_event_full_text_empty():
    assert CaptionsEvent().full_text == ""


def test_event_start_end_time():
    event = CaptionsEvent(Words=[word("a", 1000, 2000), word("b", 2500, 3000)])
    assert event.start_time == "0:00:01.00"
    assert event.end_time == "0:00:03.00"


def test_event_timing_empty_words():
    event = CaptionsEvent()
    assert event.start_time == "0:00:00.00"
    assert event.end_time == "0:00:00.00"


# --- Captions ---

def test_captions_full_text_multiple_events():
    captions = Captions(events=[
        CaptionsEvent(Words=[word("Hello", 0, 500)]),
        CaptionsEvent(Words=[word("world", 500, 1000)]),
    ])
    assert captions.full_text == "Hello world"


def test_captions_full_text_no_events():
    assert Captions().full_text == ""
