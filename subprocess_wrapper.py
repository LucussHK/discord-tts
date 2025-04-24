"""
Subprocess wrapper to completely hide console windows for all process invocations.
This module patches the subprocess module to ensure all calls to subprocesses
are executed with the appropriate flags to hide console windows on Windows.
"""

import sys
import subprocess
import functools

# Keep original references
_orig_popen = subprocess.Popen
_orig_call = subprocess.call
_orig_run = subprocess.run
_orig_check_call = subprocess.check_call
_orig_check_output = subprocess.check_output

if sys.platform == "win32":
    CREATE_NO_WINDOW  = 0x08000000
    DETACHED_PROCESS  = 0x00000008

    # 1) Subclass Popen so it remains a class for asyncio.windows_utils
    class PatchedPopen(_orig_popen):
        def __init__(self, *args, startupinfo=None, creationflags=0, **kwargs):
            # Prepare startupinfo
            if startupinfo is None:
                si = subprocess.STARTUPINFO()
            else:
                si = startupinfo
            si.dwFlags    |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0  # SW_HIDE

            # Merge creation flags
            flags = creationflags | CREATE_NO_WINDOW | DETACHED_PROCESS

            # Call original constructor
            super().__init__(*args, startupinfo=si, creationflags=flags, **kwargs)

    # Patch the module
    subprocess.Popen = PatchedPopen

    # 2) Wrap call/run/etc to inject flags too
    def _with_flags(orig_fn, *args, **kwargs):
        kwargs.setdefault('startupinfo', subprocess.STARTUPINFO())
        kwargs.setdefault('creationflags', CREATE_NO_WINDOW | DETACHED_PROCESS)
        return orig_fn(*args, **kwargs)

    subprocess.call         = functools.partial(_with_flags, _orig_call)
    subprocess.run          = functools.partial(_with_flags, _orig_run)
    subprocess.check_call   = functools.partial(_with_flags, _orig_check_call)
    subprocess.check_output = functools.partial(_with_flags, _orig_check_output)

# 3) Also patch pydub’s Popen if present
try:
    import pydub.utils
    if hasattr(pydub.utils, 'Popen'):
        _orig_pydub_popen = pydub.utils.Popen
        class PatchedPydubPopen(_orig_pydub_popen):
            def __init__(self, *args, **kwargs):
                si = kwargs.get('startupinfo', subprocess.STARTUPINFO())
                si.dwFlags    |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0
                kwargs['startupinfo']    = si
                kwargs['creationflags'] = kwargs.get('creationflags', 0) | CREATE_NO_WINDOW | DETACHED_PROCESS
                super().__init__(*args, **kwargs)
        pydub.utils.Popen = PatchedPydubPopen
except ImportError:
    pass

# 4) Patch edge-tts’s async runner if present
try:
    import edge_tts.utils
    if hasattr(edge_tts.utils, 'run_async_process'):
        _orig_edge_run = edge_tts.utils.run_async_process

        async def patched_edge_run(*args, **kwargs):
            kwargs.setdefault('creationflags', CREATE_NO_WINDOW | DETACHED_PROCESS)
            return await _orig_edge_run(*args, **kwargs)

        edge_tts.utils.run_async_process = patched_edge_run
except ImportError:
    pass
