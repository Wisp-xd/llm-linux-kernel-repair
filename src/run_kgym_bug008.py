import argparse
import json
import time
from pathlib import Path

from KBDr.kclient import JobStatus, SyzbotData, kGymClient, kJobRequest
from KBDr.kcore import JobResource
from KBDr.kclient_models.kbuilder import kBuilderArgument
from KBDr.kclient_models.kvmmanager import kVMManagerArgument


def load_bug(path: Path, bug_id: str) -> SyzbotData:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data if isinstance(data, list) else [data]
    for record in records:
        if record.get("bugId") == bug_id:
            return SyzbotData.model_validate(record)
    raise ValueError(f"bug not found: {bug_id}")


def summarize_context(variant: str, context) -> dict:
    summary = {
        "variant": variant,
        "job_id": str(context.jobId),
        "status": context.status.value,
        "current_worker": context.currentWorker,
        "workers": [],
    }
    for worker in context.jobWorkers:
        result = worker.workerResult
        item = {
            "worker_type": worker.workerType,
            "has_result": result is not None,
            "job_exception": None,
            "worker_exception": None,
        }
        if result is not None:
            if result.jobException is not None:
                item["job_exception"] = result.jobException.model_dump(mode="json")
            if result.workerException is not None:
                item["worker_exception"] = result.workerException.model_dump(mode="json")
            if worker.workerType == "kvmmanager":
                crashes = result.crashes or []
                item["image_ability"] = result.imageAbility
                item["final_syzkaller_checkout"] = result.finalSyzkallerCheckout
                item["crashes"] = [
                    {
                        "title": crash.title,
                        "crash_type": crash.crashType,
                        "incident_count": len(crash.incidents),
                    }
                    for crash in crashes
                ]
                item["reproduced_crash"] = any(
                    crash.crashType == "crash" for crash in crashes
                )
        summary["workers"].append(item)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=["parent", "developer", "llm_improved"])
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--patch", type=Path)
    parser.add_argument("--kcache-context", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--poll-seconds", type=int, default=15)
    args = parser.parse_args()

    bug = load_bug(args.dataset, "e675fbaf856bd1465eed8b8f51ae182b58b8d656")
    patch = ""
    if args.variant != "parent":
        if args.patch is None:
            raise ValueError("--patch is required for patched variants")
        patch = args.patch.read_text(encoding="utf-8").replace("\r\n", "\n")

    if args.kcache_context is None:
        builder = kBuilderArgument.model_from_syzbot_data(
            syzbot_data=bug,
            userspace_image_name="buildroot.raw",
            compiler="clang",
            linker="ld.lld",
            crash_index=0,
            commit_from="parent",
        )
    else:
        parent_context = json.loads(args.kcache_context.read_text(encoding="utf-8"))
        kcache_data = parent_context["jobWorkers"][0]["workerResult"]["kCache"]
        builder = kBuilderArgument.model_from_syzbot_data_with_kcache(
            syzbot_data=bug,
            kcache_resource=JobResource.model_validate(kcache_data),
            userspace_image_name="buildroot.raw",
        )
    builder.patch = patch
    vm = kVMManagerArgument.model_from_syzbot_data(
        syzbot_data=bug,
        machine_type="qemu:2-2048",
        image=0,
        reproducer_preference="c",
        ninstance=1,
        restart_time="5m",
        crash_index=0,
    )
    vm.reproducer.nProc = 2

    request = kJobRequest(
        jobWorkers=[builder, vm],
        tags={
            "bugId": bug.bugId,
            "experiment": "bug_008_dynamic_validation",
            "variant": args.variant,
            "kernelCommit": bug.parentOfFixCommit,
            "usesKcache": str(args.kcache_context is not None).lower(),
        },
    )
    args.output.mkdir(parents=True, exist_ok=True)
    client = kGymClient(args.api, timeout=120.0)
    job_id = client.create_job(request)
    (args.output / "job_id.txt").write_text(str(job_id) + "\n", encoding="ascii")
    print(f"submitted variant={args.variant} job_id={job_id}", flush=True)

    while True:
        context = client.get_job(job_id)
        if context is None:
            raise RuntimeError(f"job disappeared: {job_id}")
        print(
            f"status={context.status.value} worker={context.currentWorker} "
            f"host={context.currentWorkerHostname}",
            flush=True,
        )
        (args.output / "context.json").write_text(
            context.model_dump_json(indent=2), encoding="utf-8"
        )
        if context.status in (JobStatus.Finished, JobStatus.Aborted):
            summary = summarize_context(args.variant, context)
            (args.output / "summary.json").write_text(
                json.dumps(summary, indent=2), encoding="utf-8"
            )
            print(json.dumps(summary, indent=2), flush=True)
            break
        time.sleep(args.poll_seconds)
    client.close()


if __name__ == "__main__":
    main()
