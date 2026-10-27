"""Bounded validation-only CDVQA grid experiment; never writes serving assets."""
import argparse
import collections
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torchvision import transforms
from torchvision.models import resnet50


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def rows(data, split):
    assert split in ("Train", "Val")
    images = {i["id"]: i["file_name"] for i in json.loads(
        (data / f"{split}_images.json").read_text())["images"]}
    answers = {a["id"]: a["answer"] for a in json.loads(
        (data / f"{split}_answers.json").read_text())["answers"]}
    questions = json.loads((data / f"{split}_questions.json").read_text())["questions"]
    return [dict(id=q["id"], image=images[q["img_id"]], question=q["question"],
                 type=q["type"], answer=answers[q["answers_ids"][0]])
            for q in questions if q["active"]]


def metrics(pred, records, answers):
    correct = np.array([answers[p] == r["answer"] for p, r in zip(pred, records)])
    by = {t: float(correct[[i for i, r in enumerate(records) if r["type"] == t]].mean())
          for t in sorted({r["type"] for r in records})}
    return dict(oa=float(correct.mean()), aa=float(np.mean(list(by.values()))),
                by_type=by, correct=int(correct.sum()), n=len(records))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--rgb", type=Path, required=True)
    p.add_argument("--data", type=Path, default=Path("/root/satquery/cdvqa"))
    p.add_argument("--encoder", type=Path, default=Path("/root/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth"))
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error("Output must be new; no overwrites or implicit resumes.")
    assert torch.cuda.is_available()
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    torch.cuda.set_per_process_memory_fraction(6 * 1024**3 / torch.cuda.get_device_properties(0).total_memory)
    sys.path.insert(0, str(a.repo / "paired_lab"))
    from cdvqa_model import PairedAnswerModel, encode_questions, tokens
    frozen = json.loads((a.repo / "docs/EVALUATION_FREEZE_20261020.json").read_text())
    assert all(sha(a.repo / n) == h for n, h in frozen["files_sha256"].items())
    train, val = rows(a.data, "Train"), rows(a.data, "Val")
    assert (len(train), len(val)) == (65967, 16441)
    train_names, val_names = ({r["image"] for r in rs} for rs in (train, val))
    assert not train_names & val_names
    names = sorted(train_names | val_names)
    assert len(names) == 2000
    vocab = {w: i + 2 for i, w in enumerate(sorted({t for r in train for t in tokens(r["question"])}))}
    answers = sorted({r["answer"] for r in train})
    assert len(answers) == 19
    a.out.mkdir(parents=True)
    manifest = dict(
        version=1, scope="Train/Val only; test labels/predictions not parsed or evaluated; historical evidence byte-hashed only; no serving replacement",
        hypothesis="Retaining native 8x8 layer4 tokens improves validation OA versus 4x4 pooling",
        changed_variable="adaptive pooling grid only; full RGB resize remains 256x256",
        seeds=[20260928, 20260929, 20260930], variants=["question_only", "grid4", "grid8"],
        selection="maximum validation OA; strict improvement, earlier epoch breaks ties",
        optimizer=dict(name="AdamW", lr=.001, weight_decay=.01, batch=128,
                       max_epochs=35, patience=7, grad_clip=1),
        precision=dict(features="float16", head="bfloat16 autocast"),
        preprocessing="RGB resize256 bilinear, ImageNet mean/std, frozen ResNet50 IMAGENET1K_V2",
        budgets=dict(wall_seconds=2400, torch_allocated_bytes=6*1024**3,
                     output_bytes=3*1024**3, max_runs=9),
        promotion="validation evidence only; primary OA CI excludes zero, positive each seed; no >1pp AA/type regression",
        inference_controls="question only; cyclic unrelated validation pairs; exact 19-class scoring",
        exposure="benchmark weaknesses previously inspected; validation-selected estimates optimistic; no unseen claim",
        train_questions=len(train), validation_questions=len(val),
        train_pairs=len(train_names), validation_pairs=len(val_names),
        source_sha256=sha(Path(__file__)), model_source_sha256=sha(a.repo/"paired_lab/cdvqa_model.py"),
        protocol_sha256=sha(a.repo/"docs/EVALUATION_PROTOCOL_V1.md"),
        encoder_sha256=sha(a.encoder),
        labels_sha256={f"{s}_{k}.json": sha(a.data/f"{s}_{k}.json")
                       for s in ("Train", "Val") for k in ("images", "questions", "answers")},
        environment=dict(torch=torch.__version__, numpy=np.__version__, python=sys.version,
                         gpu=torch.cuda.get_device_name(0), cuda=torch.version.cuda),
        latency="No formal latency superiority claim; report extraction/training time and peak allocation",
        upstream_exposure="ImageNet pretraining exposure not independently audited")
    save(a.out/"manifest.json", manifest)
    print("MANIFEST FROZEN", sha(a.out/"manifest.json"), flush=True)
    started = time.monotonic()

    def budget():
        if time.monotonic()-started > 2400:
            raise TimeoutError("Predeclared 40 minute budget exhausted")
        if torch.cuda.max_memory_allocated() > 6*1024**3:
            raise MemoryError("Predeclared allocation ceiling exceeded")

    try:
        model = resnet50(weights=None)
        model.load_state_dict(torch.load(a.encoder, weights_only=True, map_location="cpu"))
        encoder = nn.Sequential(*list(model.children())[:-2]).eval().cuda()
        transform = transforms.Compose([
            transforms.Resize((256, 256), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(), transforms.Normalize([.485, .456, .406], [.229, .224, .225])])
        feats = {4: [], 8: []}
        input_hashes = []
        extraction = time.perf_counter()
        # Same encoder pass supplies both grids; no split-dependent normalization.
        for begin in range(0, len(names)*2, 24):
            batch = []
            for i in range(begin, min(begin+24, len(names)*2)):
                path = a.rgb/("im1" if i % 2 == 0 else "im2")/names[i//2]
                with Image.open(path) as im:
                    batch.append(transform(im.convert("RGB")))
                input_hashes.append(sha(path))
            with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
                f = encoder(torch.stack(batch).cuda())
                assert f.shape[-2:] == (8, 8)
                for grid in (4, 8):
                    feats[grid].append(nn.functional.adaptive_avg_pool2d(f, (grid, grid))
                                       .flatten(2).transpose(1, 2).cpu().half())
            budget()
            if begin % 480 == 0:
                print("FEATURES", begin, "/", len(names)*2, flush=True)
        features = {g: torch.cat(v).reshape(len(names), 2, g*g, 2048) for g, v in feats.items()}
        hashes = {n: input_hashes[i*2:i*2+2] for i, n in enumerate(names)}
        pair_hash = lambda n: hashlib.sha256("".join(hashes[n]).encode()).hexdigest()
        assert not {pair_hash(n) for n in train_names} & {pair_hash(n) for n in val_names}
        save(a.out/"input-hashes.json", hashes)
        for grid, tensor in features.items():
            torch.save(dict(names=names, features=tensor), a.out/f"features-grid{grid}.pt")
        save(a.out/"extraction.json", dict(seconds=time.perf_counter()-extraction,
             cache_sha256={str(g): sha(a.out/f"features-grid{g}.pt") for g in features}))
        del model, encoder, feats, f, batch
        torch.cuda.empty_cache()
        index = {n: i for i, n in enumerate(names)}
        amap = {a: i for i, a in enumerate(answers)}

        def tensors(rs):
            return (torch.tensor([index[r["image"]] for r in rs], device="cuda"),
                    encode_questions([r["question"] for r in rs], vocab).cuda(),
                    torch.tensor([amap[r["answer"]] for r in rs], device="cuda"))
        tr, va = tensors(train), tensors(val)
        vn = sorted(val_names)
        cyclic = {n: vn[(i+1) % len(vn)] for i, n in enumerate(vn)}
        shuffled_ids = torch.tensor([index[cyclic[r["image"]]] for r in val], device="cuda")
        summary = {}
        for seed in manifest["seeds"]:
            for label in manifest["variants"]:
                budget()
                grid = 8 if label == "grid8" else 4
                feat = features[grid].cuda()
                torch.manual_seed(seed); random.seed(seed); np.random.seed(seed)
                model = PairedAnswerModel(len(vocab)+2, len(answers), label == "question_only").cuda()
                optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.01)
                torch.cuda.reset_peak_memory_stats()
                run = a.out/f"{seed}-{label}"; run.mkdir()
                history, best, stale = [], -1, 0
                tick = time.perf_counter()

                def evaluate(ids=va[0]):
                    model.eval(); pred = []
                    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
                        for j in range(0, len(val), 256):
                            im = ids[j:j+256]
                            pred.extend(model(feat[im, 0], feat[im, 1], va[1][j:j+256])
                                        .argmax(-1).tolist())
                    return metrics(pred, val, answers), pred

                for epoch in range(1, 36):
                    model.train(); order = torch.randperm(len(train), device="cuda"); losses = []
                    for j in range(0, len(order), 128):
                        ix = order[j:j+128]; im, q, y = [t[ix] for t in tr]
                        optimizer.zero_grad(set_to_none=True)
                        with torch.autocast("cuda", dtype=torch.bfloat16):
                            loss = nn.functional.cross_entropy(model(feat[im, 0], feat[im, 1], q), y)
                        loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1)
                        optimizer.step(); losses.append(loss.item())
                        budget()
                    score, pred = evaluate()
                    history.append(dict(epoch=epoch, loss=float(np.mean(losses)), **score))
                    save(run/"history.json", history)
                    print(seed, label, epoch, round(score["oa"], 5), flush=True)
                    if score["oa"] > best:
                        best = score["oa"]; stale = 0
                        torch.save(dict(state_dict=model.cpu().state_dict(), epoch=epoch,
                                        vocab=vocab, answers=answers, grid=grid), run/"best.pt")
                        model.cuda()
                        save(run/"validation-predictions.json",
                             [dict(**r, prediction=answers[p]) for r, p in zip(val, pred)])
                    else:
                        stale += 1
                    if stale >= 7:
                        break
                checkpoint = torch.load(run/"best.pt", weights_only=True)
                model.load_state_dict(checkpoint["state_dict"])
                score, pred = evaluate()
                saved = json.loads((run/"validation-predictions.json").read_text())
                assert [answers[p] for p in pred] == [r["prediction"] for r in saved]
                shuffled, sp = evaluate(shuffled_ids)
                save(run/"shuffled-predictions.json", [dict(id=r["id"], prediction=answers[p])
                                                      for r, p in zip(val, sp)])
                summary[f"{seed}-{label}"] = dict(
                    validation=score, shuffled=shuffled, best_epoch=checkpoint["epoch"],
                    seconds=time.perf_counter()-tick, peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                    checkpoint_sha256=sha(run/"best.pt"))
                save(a.out/"summary.json", summary)
                del model, optimizer, checkpoint, feat
                torch.cuda.empty_cache()
        assert sum(p.stat().st_size for p in a.out.rglob("*") if p.is_file()) < 3*1024**3
        save(a.out/"completed.json", dict(seconds=time.monotonic()-started,
             runs=len(summary), manifest_sha256=sha(a.out/"manifest.json"), test_evaluated=False))
        print("COMPLETE", json.dumps(summary), flush=True)
    except Exception as exc:
        save(a.out/"failure.json", dict(error=repr(exc), seconds=time.monotonic()-started))
        raise


if __name__ == "__main__":
    main()
