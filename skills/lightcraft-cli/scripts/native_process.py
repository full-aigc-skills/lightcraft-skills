"""唯一原生进程监督器：流式日志、有界尾部、超时保留未知性。"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

TAIL_BYTES = 65536
MAX_LOG_BYTES = 128 * 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def supervise(argv, logs, timeout=600, tee=False, stop_file=None):
    """运行一次 argv；日志落盘，超时不推断后代退出或写入回滚。"""
    if not 0 < timeout <= 86400:
        raise ValueError('invalid_timeout')
    logs = Path(logs)
    logs.mkdir(parents=True, exist_ok=True)
    if any((logs/name).exists() or (logs/name).is_symlink() for name in ('stdout.log','stderr.log','process-start.json')):
        raise ValueError('process_logs_already_exist')
    result = {'schemaVersion': 1, 'startedAt': now(), 'argv': argv,
              'status': 'UNKNOWN', 'automaticReplay': False,
              'descendantsConfirmedStopped': False}
    tails = {}; counts = {}; failures = []; log_complete = {}
    process = None
    threads = []

    def drain(pipe, name, channel):
        tail = b''; count = 0; written=0
        try:
            with (logs / (name + '.log')).open('xb') as stream:
                while block := pipe.read1(8192):
                    kept=block[:max(0,MAX_LOG_BYTES-written)]
                    stream.write(kept);written+=len(kept)
                    count += len(block)
                    tail = (tail + block)[-TAIL_BYTES:]
                    tails[name]=tail.decode('utf-8',errors='replace');counts[name]=count
                    if tee:
                        channel.buffer.write(block); channel.buffer.flush()
                stream.flush(); os.fsync(stream.fileno())
        except (OSError, ValueError) as error:
            failures.append(str(error))
        finally:
            tails[name] = tail.decode('utf-8', errors='replace')
            counts[name] = count
            log_complete[name]=written==count
            pipe.close()

    try:
        import sys
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=(os.name == 'posix'))
        result.update(pid=process.pid, processStartedAt=now())
        result['processIdentity']=None
        if os.name=='posix':
            try:
                identity=subprocess.run(['ps','-ww','-p',str(process.pid),'-o','lstart=','-o','command='],capture_output=True,text=True,timeout=2)
                if identity.returncode==0:result['processIdentity']=identity.stdout.strip()
            except (OSError,subprocess.SubprocessError):pass
        # 进程启动事实单独持久化；调用层消失后仍可只读核对。
        start = logs / 'process-start.json'
        with start.open('x') as stream:
            json.dump(result, stream); stream.flush(); os.fsync(stream.fileno())
        for pipe, name, channel in [(process.stdout, 'stdout', sys.stdout), (process.stderr, 'stderr', sys.stderr)]:
            thread = threading.Thread(target=drain, args=(pipe, name, channel), daemon=True)
            thread.start(); threads.append(thread)
        try:
            deadline=time.monotonic()+timeout
            while process.poll() is None:
                if stop_file and Path(stop_file).exists(): raise KeyboardInterrupt('stop_requested')
                remaining=deadline-time.monotonic()
                if remaining<=0:raise subprocess.TimeoutExpired(argv,timeout)
                try:process.wait(timeout=min(.1,remaining))
                except subprocess.TimeoutExpired:pass
            result['exitCode'] = process.returncode
            result['status'] = 'EXITED'
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            result['error'] = type(error).__name__
            result['terminationScope'] = 'process-group-requested' if os.name == 'posix' else 'launch-process-only'
            try:
                if os.name == 'posix': os.killpg(process.pid, signal.SIGKILL)
                else: process.kill()
                result['exitCode'] = process.wait(timeout=5)
                result['launchProcessStopped'] = True
            except (OSError, subprocess.TimeoutExpired):
                result['launchProcessStopped'] = False
        for thread in threads:
            thread.join(timeout=2)
        if any(t.is_alive() for t in threads):
            result.update(status='UNKNOWN', error='log_stream_still_open')
        if failures:
            result.update(status='UNKNOWN', logErrors=failures)
    except OSError as error:
        result.update(error=str(error), launchProcessStarted=process is not None)
        if process is not None and process.poll() is None:
            process.kill(); process.wait(timeout=5)
    result.update(endedAt=now(), stdout=tails.get('stdout', ''), stderr=tails.get('stderr', ''),
                  stdoutBytes=counts.get('stdout', 0), stderrBytes=counts.get('stderr', 0),
                  stdoutTruncated=counts.get('stdout', 0) > TAIL_BYTES,
                  stderrTruncated=counts.get('stderr', 0) > TAIL_BYTES,
                  logDirectory=str(logs.resolve()))
    result['logComplete']=bool(log_complete) and all(log_complete.values())
    if not result['logComplete']:result.update(status='UNKNOWN',logTruncated=True)
    return result
