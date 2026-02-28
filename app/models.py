from pydantic import BaseModel

__all__ = [
    "Captions",
    "CaptionsInfo",
    "CaptionsStyle",
    "CaptionsWord",
    "CaptionsEvent",
]


def _format_ass_time(ms: int) -> str:
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    centiseconds = (ms % 1000) // 10
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

class CaptionsInfo(BaseModel):
    Title: str = "Default Title"
    WrapStyle: int = 3
    ScaledBorderAndShadow: bool = True

class CaptionsStyle(BaseModel):
    Name: str = "Default"
    Fontname: str = "Arial"
    Fontsize: int = 20
    PrimaryColour: str = "&H00FFFFFF"
    SecondaryColour: str = "&H000000FF"
    OutlineColour: str = "&H00000000"
    BackColour: str = "&H00000000"
    Bold: str = "0"
    Italic: str = "0"
    Underline: str = "0"
    StrikeOut: str = "0"
    ScaleX: str = "100"
    ScaleY: str = "100"
    Spacing: str = "0"
    Angle: str = "0"
    BorderStyle: str = "1"
    Outline: str = "1"
    Shadow: str = "0"
    Alignment: str = "2"
    MarginL: str = "10"
    MarginR: str = "10"
    MarginV: str = "10"
    Encoding: str = "1"

class CaptionsWord(BaseModel):
    text: str
    start: int
    end: int

class CaptionsEvent(BaseModel):
    Layer: str = "0"
    Style: str = "Default"
    Name: str = ""
    MarginL: str = "10"
    MarginR: str = "10"
    MarginV: str = "10"
    Effect: str = ""
    Words: list[CaptionsWord] = []

    @property
    def start_time(self) -> str:
        if not self.Words: return "0:00:00.00"
        return _format_ass_time(min(word.start for word in self.Words))
    
    @property
    def end_time(self) -> str:
        if not self.Words: return "0:00:00.00"
        return _format_ass_time(max(word.end for word in self.Words))

    @property
    def full_text(self) -> str:
        return " ".join(word.text for word in self.Words)

class Captions(BaseModel):

    info: CaptionsInfo = CaptionsInfo()
    styles: list[CaptionsStyle] = [CaptionsStyle()]
    events: list[CaptionsEvent] = []

    @property
    def full_text(self) -> str:
        return " ".join(event.full_text for event in self.events)
