from core.tools import KaraTools


def test_match_time_tool() -> None:
    tools = KaraTools()
    assert tools.match_tool("What time is it?") == "get_time"
    assert tools.match_tool("what's the time") == "get_time"


def test_match_date_tool() -> None:
    tools = KaraTools()
    assert tools.match_tool("What date is it?") == "get_date"
    assert tools.match_tool("what is today's date") == "get_date"


def test_available_unchanged() -> None:
    tools = KaraTools()
    assert "get_time" in tools.available()
    assert "get_date" in tools.available()
