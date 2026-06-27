#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small normalizers for fingerprint / exploit matching inputs."""

from __future__ import annotations

from typing import Any, Iterable, List


def as_str(value: Any, default: str = '') -> str:
    if value is None:
        return default
    if isinstance(value, list):
        return as_str(value[0], default) if value else default
    return str(value).strip()


def as_str_list(values: Iterable[Any] | None) -> List[str]:
    out: List[str] = []
    for item in values or []:
        if item is None:
            continue
        if isinstance(item, (list, tuple, set)):
            out.extend(as_str_list(item))
        else:
            s = str(item).strip()
            if s:
                out.append(s)
    return out
