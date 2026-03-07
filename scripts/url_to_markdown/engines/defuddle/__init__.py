#!/usr/bin/env python3
"""
Defuddle module for union-search-skill.

Provides Python wrapper around Defuddle CLI for web content extraction.
"""

from .defuddle_cli import url_to_markdown, DefuddleClient

__version__ = "1.0.0"
__author__ = "Claude"

__all__ = ["url_to_markdown", "DefuddleClient"]
