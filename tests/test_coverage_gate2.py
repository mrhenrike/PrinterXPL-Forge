"""Gate-2 coverage tests for PrinterXPL-Forge core modules."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# src.version
# ---------------------------------------------------------------------------

def test_version_string() -> None:
    from src.version import __version__, __version_info__, get_version, get_version_info, get_version_string
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) == 3
    assert __version_info__ == tuple(int(x) for x in __version__.split("."))
    assert get_version() == __version__
    assert get_version_info() == __version_info__
    vs = get_version_string()
    assert __version__ in vs
    assert "Version" in vs


# ---------------------------------------------------------------------------
# src.utils.normalize
# ---------------------------------------------------------------------------

def test_as_str_none() -> None:
    from src.utils.normalize import as_str
    assert as_str(None) == ""
    assert as_str(None, "fallback") == "fallback"


def test_as_str_value() -> None:
    from src.utils.normalize import as_str
    assert as_str("  hello  ") == "hello"
    assert as_str(42) == "42"


def test_as_str_list() -> None:
    from src.utils.normalize import as_str
    assert as_str(["first", "second"]) == "first"
    assert as_str([]) == ""
    assert as_str([None]) == ""


def test_as_str_list_nested() -> None:
    from src.utils.normalize import as_str_list
    result = as_str_list(["a", ["b", "c"], None, ("d",)])
    assert result == ["a", "b", "c", "d"]


def test_as_str_list_none() -> None:
    from src.utils.normalize import as_str_list
    assert as_str_list(None) == []


def test_as_str_list_empty_strings() -> None:
    from src.utils.normalize import as_str_list
    assert as_str_list(["", "  ", "ok"]) == ["ok"]


# ---------------------------------------------------------------------------
# src.utils.ports — PortConfig
# ---------------------------------------------------------------------------

def test_portconfig_defaults() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    assert PortConfig.resolve("raw") == 9100
    assert PortConfig.resolve("ipp") == 631
    assert PortConfig.resolve("snmp") == 161
    assert PortConfig.resolve("ftp") == 21
    assert PortConfig.resolve("http") == 80
    assert PortConfig.resolve("https") == 443
    assert PortConfig.resolve("smb") == 445
    assert PortConfig.resolve("telnet") == 23
    assert PortConfig.resolve("wsd") == 3702
    assert PortConfig.resolve("lpd") == 515


def test_portconfig_aliases() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    assert PortConfig.resolve("pjl") == 9100
    assert PortConfig.resolve("jetdirect") == 9100
    assert PortConfig.resolve("lpr") == 515
    assert PortConfig.resolve("9100") == 9100


def test_portconfig_configure_override() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    PortConfig.configure(raw=3910, snmp=1161)
    assert PortConfig.resolve("raw") == 3910
    assert PortConfig.resolve("snmp") == 1161
    assert PortConfig.default("raw") == 9100
    PortConfig.reset()


def test_portconfig_configure_extra() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    PortConfig.configure(extra={12345, 54321})
    extras = PortConfig.extra_scan_ports()
    assert 12345 in extras
    assert 54321 in extras
    PortConfig.reset()


def test_portconfig_invalid_port() -> None:
    from src.utils.ports import PortConfig
    import pytest
    PortConfig.reset()
    with pytest.raises(ValueError):
        PortConfig.configure(raw=0)
    with pytest.raises(ValueError):
        PortConfig.configure(raw=70000)
    PortConfig.reset()


def test_portconfig_fallback() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    assert PortConfig.resolve("unknown_proto") == 9100
    assert PortConfig.resolve("unknown_proto", fallback=8888) == 8888


def test_portconfig_all_printer_ports() -> None:
    from src.utils.ports import PortConfig, GLOBAL_PRINTER_TCP_PORTS
    PortConfig.reset()
    ports = PortConfig.all_printer_ports()
    assert isinstance(ports, set)
    assert 9100 in ports
    assert 80 in ports
    for p in GLOBAL_PRINTER_TCP_PORTS:
        assert p in ports


def test_portconfig_printer_port_labels() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    labels = PortConfig.printer_port_labels()
    assert isinstance(labels, dict)
    assert 9100 in labels
    assert 80 in labels


def test_portconfig_summary() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    s = PortConfig.summary()
    assert "raw" in s
    assert "9100" in s


def test_portconfig_configure_from_args() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    args = SimpleNamespace(port_raw=3910, port_ipp=None, port_lpd=None,
                           port_snmp=None, port_ftp=None, port_http=None,
                           port_https=None, port_smb=None, port_telnet=None,
                           port_wsd=None, extra_ports=[7777])
    PortConfig.configure_from_args(args)
    assert PortConfig.resolve("raw") == 3910
    assert 7777 in PortConfig.extra_scan_ports()
    PortConfig.reset()


def test_portconfig_summary_with_override() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    PortConfig.configure(raw=3910, extra={11111})
    s = PortConfig.summary()
    assert "custom: 3910" in s
    assert "extra" in s
    assert "11111" in s
    PortConfig.reset()


def test_portconfig_labels_with_override() -> None:
    from src.utils.ports import PortConfig
    PortConfig.reset()
    PortConfig.configure(raw=3910, extra={22222})
    labels = PortConfig.printer_port_labels()
    assert 3910 in labels
    assert labels[3910] == "RAW"
    assert 22222 in labels
    assert "Custom" in labels[22222]
    PortConfig.reset()


# ---------------------------------------------------------------------------
# src.utils.helper — item, chunks, conv, output.strfit
# ---------------------------------------------------------------------------

def test_item_first() -> None:
    from src.utils.helper import item
    assert item([1, 2, 3]) == 1
    assert item([], "alt") == "alt"
    assert item(iter(["a", "b"])) == "a"


def test_chunks() -> None:
    from src.utils.helper import chunks
    result = list(chunks([1, 2, 3, 4, 5], 2))
    assert result == [[1, 2], [3, 4], [5]]


def test_conv_int() -> None:
    from src.utils.helper import conv
    c = conv()
    assert c.int("42") == 42
    assert c.int("abc") == 0
    assert c.int(0) == 0


def test_conv_hex() -> None:
    from src.utils.helper import conv
    c = conv()
    assert c.hex("AB") == "4142"
    assert c.hex("AB", ":") == "41:42"


def test_conv_chr() -> None:
    from src.utils.helper import conv
    c = conv()
    assert c.chr(65) == "A"
    assert c.chr("66") == "B"


def test_conv_nstrip() -> None:
    from src.utils.helper import conv
    c = conv()
    assert c.nstrip("hello\r\nworld\r\n") == "hello\nworld\n"


def test_conv_filesize() -> None:
    from src.utils.helper import conv
    c = conv()
    assert "B" in c.filesize(500)
    assert "K" in c.filesize(2048)
    assert "M" in c.filesize(2 * 1024 * 1024)


def test_conv_now() -> None:
    import time
    from src.utils.helper import conv
    c = conv()
    assert abs(c.now() - int(time.time())) <= 1


def test_conv_elapsed() -> None:
    from src.utils.helper import conv
    c = conv()
    result = c.elapsed(3661)
    assert "1:01:01" in result


def test_conv_elapsed_short() -> None:
    from src.utils.helper import conv
    c = conv()
    result = c.elapsed(90061, short=True)
    assert "," not in result


def test_output_strfit() -> None:
    from src.utils.helper import output
    o = output()
    assert o.strfit("hello", 10) == "hello     "
    assert len(o.strfit("a" * 50, 10)) == 10
    assert o.strfit("", 5) == "-    "
    assert o.strfit("(wrapped)", 20) == "wrapped             "


# ---------------------------------------------------------------------------
# src.utils.fuzzer — fuzzer class
# ---------------------------------------------------------------------------

def test_fuzzer_static_lists() -> None:
    from src.utils.fuzzer import fuzzer
    f = fuzzer()
    assert len(f.vol) > 0
    assert len(f.var) > 0
    assert len(f.win) > 0
    assert len(f.smb) > 0
    assert len(f.web) > 0
    assert len(f.dir) > 0
    assert len(f.sep) > 0
    assert len(f.fhs) > 0
    assert len(f.path) > 0
    assert len(f.write) > 0
    assert len(f.blind) > 0


def test_fuzzer_fuzz_paths() -> None:
    from src.utils.fuzzer import fuzzer
    f = fuzzer()
    paths = f.fuzz_paths()
    assert isinstance(paths, list)
    assert len(paths) > 50
    assert any("etc/passwd" in p for p in paths if isinstance(p, str))


def test_fuzzer_fuzz_names() -> None:
    from src.utils.fuzzer import fuzzer
    f = fuzzer()
    names = f.fuzz_names()
    assert isinstance(names, list)
    assert any("passwd" in n for n in names)
    assert any(len(n) > 200 for n in names)


def test_fuzzer_fuzz_data_sizes() -> None:
    from src.utils.fuzzer import fuzzer
    f = fuzzer()
    small = f.fuzz_data("small")
    medium = f.fuzz_data("medium")
    assert isinstance(small, bytes)
    assert len(small) == 1000
    assert len(medium) == 10000


def test_fuzzer_fuzz_traversal_vectors() -> None:
    from src.utils.fuzzer import fuzzer
    f = fuzzer()
    vectors = f.fuzz_traversal_vectors()
    assert isinstance(vectors, list)
    assert len(vectors) > 30
    assert any("etc/passwd" in v for v in vectors)
    assert any("windows" in v.lower() for v in vectors)


# ---------------------------------------------------------------------------
# src.core.discovery — parse_selection
# ---------------------------------------------------------------------------

def test_parse_selection_all() -> None:
    from src.core.discovery import parse_selection
    assert parse_selection("all", 5) == [1, 2, 3, 4, 5]
    assert parse_selection("a", 3) == [1, 2, 3]
    assert parse_selection("", 4) == [1, 2, 3, 4]


def test_parse_selection_individual() -> None:
    from src.core.discovery import parse_selection
    assert parse_selection("2", 5) == [2]
    assert parse_selection("1,3,5", 5) == [1, 3, 5]


def test_parse_selection_range() -> None:
    from src.core.discovery import parse_selection
    assert parse_selection("2-4", 5) == [2, 3, 4]
    assert parse_selection("1-3,5", 5) == [1, 2, 3, 5]


def test_parse_selection_bounds() -> None:
    from src.core.discovery import parse_selection
    result = parse_selection("1,10,100", 5)
    assert result == [1]


# ---------------------------------------------------------------------------
# src.utils.ports — GLOBAL_PRINTER_TCP_PORTS dict
# ---------------------------------------------------------------------------

def test_global_printer_tcp_ports() -> None:
    from src.utils.ports import GLOBAL_PRINTER_TCP_PORTS
    assert isinstance(GLOBAL_PRINTER_TCP_PORTS, dict)
    assert 9100 in GLOBAL_PRINTER_TCP_PORTS
    assert 80 in GLOBAL_PRINTER_TCP_PORTS
    assert 443 in GLOBAL_PRINTER_TCP_PORTS
    assert all(isinstance(k, int) for k in GLOBAL_PRINTER_TCP_PORTS)
    assert all(isinstance(v, str) for v in GLOBAL_PRINTER_TCP_PORTS.values())
