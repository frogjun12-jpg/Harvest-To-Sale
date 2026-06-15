"""
finetune_chronos_official.py

공식 Chronos fine-tuning 파이프라인
1. CSV → Arrow 파일 변환
2. baseline (상+중) / extended (특+상+중+하) 두 가지 config 생성
3. 공식 train.py 실행

사전 준비:
    git clone https://github.com/amazon-science/chronos-forecasting.git
    cd chronos-forecasting
    pip install --editable ".[training]"
"""

import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

DATA_DIR   = Path("preprocessed_data")
ARROW_DIR  = Path("arrow_data")
CONFIG_DIR = Path("configs")
OUTPUT_DIR = Path("finetuned_model")

ARROW_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ────────────────────────────────
# 1. CSV → Arrow 변환
# ────────────────────────────────
def csv_to_arrow(grade: str, window: int) -> Path | None:
    path = DATA_DIR / f"garak_apple_{grade}_w{window}.csv"
    if not path.exists():
        print(f"  파일 없음: {path}")
        return None

    df = pd.read_csv(path)
    df = df.sort_values("date").reset_index(drop=True)

    if len(df) < 50:
        print(f"  [{grade}] w{window} 건수 부족 ({len(df)}건) → 제외")
        return None

    # Chronos Arrow 포맷: start(timestamp), target(list of float)
    table = pa.table({
        "start": pa.array([pd.Timestamp("2000-01-01")], type=pa.timestamp("s")),
        "target": pa.array([df["price_per_kg"].astype(float).values.tolist()], type=pa.list_(pa.float64()))
    })

    out_path = ARROW_DIR / f"{grade}_w{window}.arrow"
    with pa.ipc.new_file(out_path, table.schema) as writer:
        writer.write_table(table)

    print(f"  [{grade}] w{window} → {len(df)}건 → {out_path}")
    return out_path


def build_arrow_files(grades: list[str]) -> list[Path]:
    paths = []
    for grade in grades:
        for w in [0, 1, 2]:
            p = csv_to_arrow(grade, w)
            if p:
                paths.append(p)
    return paths


# ────────────────────────────────
# 2. YAML Config 생성
# ────────────────────────────────
def build_yaml(arrow_paths: list[Path], save_name: str, max_steps: int = 1000) -> Path:
    data_paths = "\n".join([f'  - "{p.resolve()}"' for p in arrow_paths])
    probs = "\n".join([f"  - {1.0 / len(arrow_paths):.4f}" for _ in arrow_paths])

    yaml_content = f"""# Chronos fine-tuning config: {save_name}

training_data_paths:
{data_paths}

probability:
{probs}

context_length: 512
prediction_length: 30
min_past: 60
max_steps: {max_steps}
save_steps: {max_steps // 5}
log_steps: 50

per_device_train_batch_size: 8
learning_rate: 1.0e-4
optim: adamw_torch
num_samples: 20
shuffle_buffer_length: 1000
gradient_accumulation_steps: 2

model_id: amazon/chronos-t5-mini
model_type: seq2seq
random_init: false        # pretrained에서 시작 (fine-tuning)
tie_embeddings: true

output_dir: {(OUTPUT_DIR / save_name).resolve()}

lr_scheduler_type: linear
warmup_ratio: 0.1
dataloader_num_workers: 1
max_missing_prop: 0.9
use_eos_token: true

tokenizer_class: "MeanScaleUniformBins"
tokenizer_kwargs:
  low_limit: -15.0
  high_limit: 15.0
  n_tokens: 4096
"""

    config_path = CONFIG_DIR / f"{save_name}.yaml"
    config_path.write_text(yaml_content, encoding="utf-8")
    print(f"  Config 저장: {config_path}")
    return config_path


# ────────────────────────────────
# 3. 메인
# ────────────────────────────────
if __name__ == "__main__":

    # ── Baseline: 상 + 중 ──
    print("\n[Baseline] Arrow 변환: 상 + 중")
    baseline_paths = build_arrow_files(["상", "중"])
    print(f"  총 {len(baseline_paths)}개 시계열")

    print("\n[Baseline] Config 생성")
    baseline_config = build_yaml(baseline_paths, "chronos_baseline", max_steps=1000)

    # ── Extended: 특 + 상 + 중 + 하 ──
    print("\n[Extended] Arrow 변환: 특 + 상 + 중 + 하")
    extended_paths = build_arrow_files(["특", "상", "중", "하"])
    print(f"  총 {len(extended_paths)}개 시계열")

    print("\n[Extended] Config 생성")
    extended_config = build_yaml(extended_paths, "chronos_extended", max_steps=1000)

    # ── 실행 안내 ──
    print("\n" + "="*60)
    print("fine-tuning 실행 명령어:")
    print("="*60)
    print("\n# 1. chronos-forecasting 클론 및 설치")
    print("git clone https://github.com/amazon-science/chronos-forecasting.git")
    print("cd chronos-forecasting")
    print('pip install --editable ".[training]"')
    print("\n# 2. Baseline fine-tuning")
    print(f"python scripts/training/train.py --config {baseline_config.resolve()}")
    print("\n# 3. Extended fine-tuning")
    print(f"python scripts/training/train.py --config {extended_config.resolve()}")
