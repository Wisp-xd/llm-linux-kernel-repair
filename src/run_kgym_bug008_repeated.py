import argparse
import json
import time
from pathlib import Path

from KBDr.kclient import JobStatus, kGymClient, kJobRequest
from KBDr.kclient_models.kvmmanager import Image, Reproducer, kVMManagerArgument
from KBDr.kcore import JobResource


TARGET_CRASH = "KASAN: null-ptr-deref Read in sys_mount_setattr"


def bounded_reproducer(
    source: str,
    runtime_seconds: int,
    heartbeat_seconds: int,
    loop_delay_ms: int = 0,
) -> str:
    old_header = """static void loop(void)
{
  int iter = 0;
  for (;; iter++) {
"""
    loop_condition = (
        "; current_time_ms() < deadline; iter++"
        if runtime_seconds > 0
        else ";; iter++"
    )
    deadline = (
        f"  uint64_t deadline = started + {runtime_seconds}ULL * 1000;\n"
        if runtime_seconds > 0
        else ""
    )
    loop_delay = f"    sleep_ms({loop_delay_ms});\n" if loop_delay_ms > 0 else ""
    new_header = f"""static void loop(void)
{{
  int iter = 0;
  uint64_t started = current_time_ms();
{deadline}  uint64_t next_heartbeat = started;
  for ({loop_condition}) {{
    uint64_t now = current_time_ms();
    if (now >= next_heartbeat) {{
      dprintf(STDOUT_FILENO,
              "executing program: KGYM_HEARTBEAT elapsed_ms=%llu iter=%d\\n",
              (unsigned long long)(now - started), iter);
      next_heartbeat = now + {heartbeat_seconds}ULL * 1000;
    }}
{loop_delay}"""
    if source.count(old_header) != 1:
        raise ValueError("unexpected reproducer loop header")
    source = source.replace(old_header, new_header, 1)

    main_header = """int main(void)
{
"""
    heartbeat_main = f"""static void start_heartbeat(void)
{{
  int parent = getpid();
  int pid = fork();
  if (pid < 0)
    exit(1);
  if (pid != 0)
    return;
  prctl(PR_SET_PDEATHSIG, SIGKILL, 0, 0, 0);
  if (getppid() != parent)
    _exit(0);
  uint64_t started = current_time_ms();
  for (unsigned long long seq = 0;; seq++) {{
    dprintf(STDOUT_FILENO,
            "executing program: KGYM_HEARTBEAT_INDEPENDENT "
            "elapsed_ms=%llu seq=%llu\\n",
            (unsigned long long)(current_time_ms() - started), seq);
    sleep({heartbeat_seconds});
  }}
}}

int main(void)
{{
  start_heartbeat();
"""
    if source.count(main_header) != 1:
        raise ValueError("unexpected reproducer main header")
    source = source.replace(main_header, heartbeat_main, 1)

    if runtime_seconds <= 0:
        return source

    old_tail = """      break;
    }
  }
}

uint64_t r[1]"""
    new_tail = """      break;
    }
  }
  dprintf(STDOUT_FILENO, "KGYM_COMPLETED runtime_ms=%llu iterations=%d\\n",
          (unsigned long long)(current_time_ms() - started), iter);
}

uint64_t r[1]"""
    if source.count(old_tail) != 1:
        raise ValueError("unexpected reproducer loop tail")
    return source.replace(old_tail, new_tail, 1)


def load_base(context_path: Path) -> tuple[Image, Reproducer, str]:
    context = json.loads(context_path.read_text(encoding="utf-8"))
    builder_result = context["jobWorkers"][0]["workerResult"]
    old_reproducer = context["jobWorkers"][1]["workerArgument"]["reproducer"]
    image = Image(
        vmImage=JobResource.model_validate(builder_result["vmImage"]),
        vmlinux=JobResource.model_validate(builder_result["vmlinux"]),
        arch=builder_result["kernelArch"],
    )
    reproducer = Reproducer.model_validate(old_reproducer)
    return image, reproducer, context["tags"]["kernelCommit"]


def summarize(context, run_index: int, runtime_seconds: int) -> dict:
    worker = context.jobWorkers[0]
    result = worker.workerResult
    crashes = [] if result is None else (result.crashes or [])
    target_crashes = [crash for crash in crashes if crash.title == TARGET_CRASH]
    special_crashes = [crash for crash in crashes if crash.crashType == "special"]
    exceptions = []
    if result is not None:
        if result.jobException is not None:
            exceptions.append(result.jobException.model_dump(mode="json"))
        if result.workerException is not None:
            exceptions.append(result.workerException.model_dump(mode="json"))
    return {
        "run_index": run_index,
        "runtime_seconds": runtime_seconds,
        "job_id": str(context.jobId),
        "status": context.status.value,
        "image_ability": None if result is None else result.imageAbility,
        "target_crash_reproduced": bool(target_crashes),
        "special_crashes": [crash.title for crash in special_crashes],
        "all_crashes": [
            {"title": crash.title, "crash_type": crash.crashType}
            for crash in crashes
        ],
        "exceptions": exceptions,
        "clean_pass": (
            context.status == JobStatus.Finished
            and result is not None
            and not crashes
            and not exceptions
            and result.imageAbility == "normal"
        ),
    }


def run_once(
    client: kGymClient,
    image: Image,
    base_reproducer: Reproducer,
    kernel_commit: str,
    output_dir: Path,
    run_index: int,
    runtime_seconds: int,
    heartbeat_seconds: int,
    loop_delay_ms: int,
    restart_time: str,
    poll_seconds: int,
) -> dict:
    source = bounded_reproducer(
        base_reproducer.reproducerText,
        runtime_seconds,
        heartbeat_seconds,
        loop_delay_ms,
    )
    reproducer = base_reproducer.model_copy(deep=True)
    reproducer.reproducerText = source
    reproducer.restartTime = restart_time
    reproducer.nInstance = 1
    reproducer.nProc = 2
    vm = kVMManagerArgument(
        reproducer=reproducer,
        image=image,
        machineType="qemu:2-2048",
    )
    request = kJobRequest(
        jobWorkers=[vm],
        tags={
            "bugId": "e675fbaf856bd1465eed8b8f51ae182b58b8d656",
            "experiment": "bug_008_repeated_dynamic_validation",
            "variant": "llm_improved_heartbeat",
            "kernelCommit": kernel_commit,
            "runIndex": str(run_index),
            "runtimeSeconds": str(runtime_seconds),
            "heartbeatSeconds": str(heartbeat_seconds),
            "loopDelayMs": str(loop_delay_ms),
            "reusesJob": "0000000a",
        },
    )
    run_dir = output_dir / f"run_{run_index:02d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "reproducer.c").write_text(source, encoding="utf-8")
    job_id = client.create_job(request)
    (run_dir / "job_id.txt").write_text(str(job_id) + "\n", encoding="ascii")
    print(f"submitted run={run_index} job_id={job_id}", flush=True)
    while True:
        context = client.get_job(job_id)
        if context is None:
            raise RuntimeError(f"job disappeared: {job_id}")
        (run_dir / "context.json").write_text(
            context.model_dump_json(indent=2), encoding="utf-8"
        )
        print(
            f"run={run_index} status={context.status.value} "
            f"worker={context.currentWorker} host={context.currentWorkerHostname}",
            flush=True,
        )
        if context.status in (JobStatus.Finished, JobStatus.Aborted):
            summary = summarize(context, run_index, runtime_seconds)
            (run_dir / "summary.json").write_text(
                json.dumps(summary, indent=2), encoding="utf-8"
            )
            print(json.dumps(summary, indent=2), flush=True)
            return summary
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--runtime-seconds", type=int, default=300)
    parser.add_argument("--heartbeat-seconds", type=int, default=10)
    parser.add_argument("--loop-delay-ms", type=int, default=0)
    parser.add_argument("--restart-time", default="8m")
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--stop-on-non-clean", action="store_true")
    args = parser.parse_args()

    image, reproducer, kernel_commit = load_base(args.context)
    args.output.mkdir(parents=True, exist_ok=True)
    client = kGymClient(args.api, timeout=120.0)
    summaries = []
    try:
        for run_index in range(1, args.runs + 1):
            summary = run_once(
                    client,
                    image,
                    reproducer,
                    kernel_commit,
                    args.output,
                    run_index,
                    args.runtime_seconds,
                    args.heartbeat_seconds,
                    args.loop_delay_ms,
                    args.restart_time,
                    args.poll_seconds,
                )
            summaries.append(summary)
            if args.stop_on_non_clean and not summary["clean_pass"]:
                print("stopping repeated validation after non-clean run", flush=True)
                break
    finally:
        client.close()
    aggregate = {
        "runs": summaries,
        "run_count": len(summaries),
        "clean_pass_count": sum(item["clean_pass"] for item in summaries),
        "target_crash_count": sum(
            item["target_crash_reproduced"] for item in summaries
        ),
        "special_crash_count": sum(bool(item["special_crashes"]) for item in summaries),
        "all_clean": bool(summaries) and all(item["clean_pass"] for item in summaries),
    }
    (args.output / "aggregate_summary.json").write_text(
        json.dumps(aggregate, indent=2), encoding="utf-8"
    )
    print(json.dumps(aggregate, indent=2), flush=True)


if __name__ == "__main__":
    main()
