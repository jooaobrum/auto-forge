---
name: lp-ft-finetune
profile: image
status: experimental
---

# lp-ft-finetune

## When to use
The backbone is already chosen; the linear probe is not enough and you want fine-tuning without losing out-of-distribution robustness.

## Typical hypotheses
- LP-FT: first the linear probe with the backbone frozen, then full fine-tuning from that head, with a low learning rate.
- Compare LP-FT with the linear probe and with direct fine-tuning.

## Probe and budget
Hyperparameters (learning rate, epochs, unfrozen layers) on valid only. In Kumar et al. (ICLR 2022) full fine-tuning gained ~2% in distribution and lost ~7% out of distribution against the linear probe; LP-FT ended ~10% above fine-tuning out of distribution.
Budget: 1 LP probe, 2-3 FT probes.

## Required checks
- `CHK-OOT-002` - Drop between valid and OOT within the plan's limit

## Traps
- Direct fine-tuning with a random head distorts the pretrained features.
- The plan's valid-to-OOT drop applies here (CHK-OOT-002): this is where fine-tuning usually pays the bill.

## Source
Kumar et al., Fine-Tuning can Distort Pretrained Features and Underperform Out-of-Distribution (ICLR 2022); Recipe 10 of experimenta-ml.

## Examples
_No runs yet. A recipe leaves `experimental` when it has repeatable runs here and passes review._
