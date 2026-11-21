# Short-input slice

**Profile**: model
**Lane**: research
**Approved**: 2026-11-22 - user: "go"
**Failure mode**: short inputs misclassified at the global threshold
**Target cases**: short
**k**: target 3, affected 3, stable 1

## Goal

Short inputs are classified as well as long ones.

## Diagnosis

The short slice's labels flip at a lower score than the global threshold assumes. Cause class: behavioral
(a parameter).

## Cases

| Case | Question | Rubric | Tier |
| --- | --- | --- | --- |
| short | inputs under 20 tokens | accuracy at the bar | capability |
| long | inputs of 20 tokens or more | accuracy at the bar | regression |
| rare | rare classes | accuracy at the bar | capability |

## Metrics

| Metric | Pass at | Guardrail | Target |
| --- | --- | --- | --- |
| accuracy | | | +0.03 |
