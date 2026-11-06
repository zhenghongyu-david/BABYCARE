"""Register the bundled Noto Sans SC font with Kivy.

The two static weights are distributed under the SIL Open Font License.  They
are bundled instead of relying on a system font so the app looks the same on
every Android phone and on the desktop preview.
"""
from __future__ import annotations

from pathlib import Path

from kivy.core.text import LabelBase

from . import theme


def _find_fonts() -> tuple[Path | None, Path | None]:
    assets = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    regular = assets / "NotoSansSC-Regular.ttf"
    bold = assets / "NotoSansSC-Bold.ttf"
    if regular.exists():
        return regular, bold if bold.exists() else regular

    candidates = [
        Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("/system/fonts/NotoSansCJK-Regular.ttc"),
        Path("/system/fonts/NotoSansSC-Regular.otf"),
        Path("/system/fonts/NotoSansCJKsc-Regular.otf"),
    ]
    found = next((path for path in candidates if path.exists()), None)
    return found, found


def register_fonts() -> None:
    regular, bold = _find_fonts()
    if not regular:
        return
    regular = str(regular)
    bold = str(bold or regular)
    LabelBase.register(
        name=theme.FONT_CN,
        fn_regular=regular,
        fn_bold=bold,
    )
    LabelBase.register(name=theme.FONT_CN_BOLD, fn_regular=bold)
    # Numerals share the same humanist skeleton as the Chinese glyphs.
    LabelBase.register(name=theme.FONT_NUM, fn_regular=bold)
