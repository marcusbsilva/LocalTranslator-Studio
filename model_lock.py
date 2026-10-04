"""Prevent competing CLI and web model mutations across processes."""
import os
from contextlib import contextmanager
from paths import DATA
@contextmanager
def management_lock():
 DATA.mkdir(parents=True,exist_ok=True)
 with (DATA/'.model-management.lock').open('a+b') as handle:
  handle.seek(0)
  if not handle.read(1):handle.write(b'0');handle.flush()
  handle.seek(0)
  try:
   if os.name=='nt':
    import msvcrt
    msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
   else:
    import fcntl
    fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except OSError:raise RuntimeError('Another model operation is running. Wait for it to finish.')
  try:yield
  finally:
   if os.name=='nt':handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
   else:fcntl.flock(handle,fcntl.LOCK_UN)
