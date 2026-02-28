from app.models import _format_ass_time, CaptionsWord, CaptionsEvent, CaptionsInfo, Captions, BurnRequest, BurnJob


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


# --- Captions.to_ass() ---

def test_to_ass_has_sections():
    ass = Captions().to_ass()
    assert "[Script Info]" in ass
    assert "[V4+ Styles]" in ass
    assert "[Events]" in ass


def test_to_ass_has_format_lines():
    ass = Captions().to_ass()
    assert "Format: Name, Fontname" in ass
    assert "Format: Layer, Start" in ass


def test_to_ass_title():
    captions = Captions(info=CaptionsInfo(Title="My Video"))
    assert "Title: My Video" in captions.to_ass()


def test_to_ass_scaled_border_yes():
    captions = Captions(info=CaptionsInfo(ScaledBorderAndShadow=True))
    assert "ScaledBorderAndShadow: yes" in captions.to_ass()


def test_to_ass_scaled_border_no():
    captions = Captions(info=CaptionsInfo(ScaledBorderAndShadow=False))
    assert "ScaledBorderAndShadow: no" in captions.to_ass()


def test_to_ass_default_style_line():
    ass = Captions().to_ass()
    assert "Style: Default,Arial,20" in ass


def test_to_ass_event_dialogue():
    captions = Captions(events=[
        CaptionsEvent(Words=[word("Hello", 0, 1000), word("world", 1000, 2000)])
    ])
    ass = captions.to_ass()
    assert "Dialogue:" in ass
    assert "Hello world" in ass


def test_to_ass_event_timing():
    captions = Captions(events=[
        CaptionsEvent(Words=[word("Hi", 500, 1500)])
    ])
    ass = captions.to_ass()
    assert "0:00:00.50" in ass   # start
    assert "0:00:01.50" in ass   # end


def test_to_ass_no_events_no_dialogue():
    assert "Dialogue:" not in Captions().to_ass()


def test_to_ass_multiple_events():
    captions = Captions(events=[
        CaptionsEvent(Words=[word("A", 0, 500)]),
        CaptionsEvent(Words=[word("B", 500, 1000)]),
    ])
    assert captions.to_ass().count("Dialogue:") == 2


# --- BurnRequest ---

def test_burn_request():
    req = BurnRequest(video_url="https://example.com/video.mp4")
    assert req.video_url == "https://example.com/video.mp4"


# --- BurnJob ---

def test_burn_job_defaults():
    job = BurnJob(id="j1", caption_id="c1", status="pending")
    assert job.output_url is None
    assert job.error is None


def test_burn_job_done():
    job = BurnJob(id="j1", caption_id="c1", status="done", output_url="https://gcs.example.com/file.mp4")
    assert job.output_url == "https://gcs.example.com/file.mp4"


def test_burn_job_failed():
    job = BurnJob(id="j1", caption_id="c1", status="failed", error="FFmpeg crashed")
    assert job.error == "FFmpeg crashed"
