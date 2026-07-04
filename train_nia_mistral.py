"""
train_nia_mistral.py — LoRA hardening for Nia: The Minister of Verdicts

Base model: mistralai/Mistral-7B-Instruct-v0.3
Target:     Burn the Nia persona into the weights.

Run on RunPod (A100/A40/RTX 4090/5090).

Usage:
    python train_nia_mistral.py
    python train_nia_mistral.py --resume_from_checkpoint checkpoints/nia-mistral-lora/checkpoint-5000
"""

import argparse
import json

import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainingArguments,
)

BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
OUTPUT_DIR = "checkpoints/nia-mistral-lora"
DEFAULT_DATA = "data/nia_full_dataset.jsonl"

LORA_CONFIG = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)

MAX_LENGTH = 1024


def load_jsonl(path: str) -> list:
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def format_record(example, tokenizer) -> str:
    if "messages" in example:
        return tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
    # system/instruction/response format
    messages = []
    if example.get("system") and isinstance(example["system"], str):
        messages.append({"role": "system", "content": example["system"]})
    messages.append({"role": "user", "content": example.get("instruction") or ""})
    messages.append({"role": "assistant", "content": example.get("response") or ""})
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )


def tokenize(examples, tokenizer):
    texts = [format_record({k: examples[k][i] for k in examples}, tokenizer)
             for i in range(len(next(iter(examples.values()))))]
    tokenized = tokenizer(
        texts,
        truncation=True,
        max_length=MAX_LENGTH,
        padding=False,
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=DEFAULT_DATA)
    parser.add_argument("--base", default=BASE_MODEL)
    parser.add_argument("--output", default=OUTPUT_DIR)
    parser.add_argument("--steps", type=int, default=6340)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--resume_from_checkpoint", type=str, default=None)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    print(f"Device: {device} | dtype: {dtype}")

    print(f"Loading base model: {args.base}")
    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
    )
    model = get_peft_model(model, LORA_CONFIG)
    model.print_trainable_parameters()

    print(f"Loading data: {args.data}")
    raw = load_jsonl(args.data)
    dataset = Dataset.from_list(raw)
    dataset = dataset.map(
        lambda ex: tokenize(ex, tokenizer),
        batched=True,
        remove_columns=dataset.column_names,
    )

    split = dataset.train_test_split(test_size=0.02, seed=42)
    train_ds = split["train"]
    eval_ds = split["test"]
    print(f"Train: {len(train_ds)} | Eval: {len(eval_ds)}")

    training_args = TrainingArguments(
        output_dir=args.output,
        max_steps=args.steps,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        bf16=(device == "cuda"),
        fp16=False,
        logging_steps=20,
        eval_strategy="steps",
        eval_steps=200,
        save_steps=400,
        save_total_limit=3,
        load_best_model_at_end=True,
        report_to="none",
        dataloader_num_workers=0,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8),
    )

    print("Starting Nia Mistral-7B LoRA hardening...")
    trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)

    print(f"Saving adapter to {args.output}")
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    print("Done. Nia is hardened.")


if __name__ == "__main__":
    main()
