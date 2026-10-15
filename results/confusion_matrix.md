# Deflection assistant - confusion matrix

Operating confidence threshold: **0.55** (chosen by the sweep in `results/assistant_eval.json`).

| expected \ predicted | Order Status | Return | Warranty | Shipping | Sizing | Store Hours | escalate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Order Status** | 19 | 0 | 0 | 0 | 0 | 0 | 1 |
| **Return** | 0 | 20 | 0 | 0 | 0 | 0 | 0 |
| **Warranty** | 0 | 0 | 19 | 0 | 0 | 0 | 1 |
| **Shipping** | 0 | 0 | 0 | 20 | 0 | 0 | 0 |
| **Sizing** | 0 | 0 | 0 | 0 | 20 | 0 | 0 |
| **Store Hours** | 0 | 0 | 0 | 0 | 0 | 20 | 0 |
| **escalate** | 0 | 0 | 0 | 0 | 0 | 1 | 19 |
