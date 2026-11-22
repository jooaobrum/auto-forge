---
name: backbone-selection
profile: image
status: experimental
---

# backbone-selection

## When to use
Choosing the pretrained backbone for an image problem. This is a user decision backed by evidence, not an optimization.

## Typical hypotheses
- Compare 2-4 candidate backbones (e.g. ResNet-50, ViT-B/16, ConvNeXt-T, DINOv2) through frozen embeddings.

## Probe and budget
Extract frozen embeddings from each candidate for train and valid and train a **linear probe** (logistic regression) on train; metric on valid. It fits on CPU with a small dataset.
Budget: 1 probe per backbone. The hypothesis stays `Status: decision` until the user chooses (`- Decision: user - <backbone>`).

## Required checks
- `CHK-DUP-002` - No near-duplicates between splits (embedding similarity)

## Traps
- Near-duplicates between splits inflate the linear probe (CHK-DUP-002, embedding similarity).
- Comparing backbones with different preprocessing without saying so.
- Choosing by the OOT.

## Source
Alchemist's architecture sweep and Recipe 10 of experimenta-ml.

## Examples
_No runs yet. A recipe leaves `experimental` when it has repeatable runs here and passes review._
