#!/usr/bin/env python3
"""Standalone entrypoint for TailSend GUI (delegates to app.py --tailsend)."""
import os
import sys

APP_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
os.execv(sys.executable, [sys.executable, APP_PY, "--tailsend"] + sys.argv[1:])
