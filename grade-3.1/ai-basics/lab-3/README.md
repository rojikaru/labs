# Particle filter for Robot Localization

Test it via:

```bash
cd /mnt/shared/dev/labs/grade-3.1/ai-basics/lab-3 && cargo build --release 2>&1 && echo "" && echo "Testing all inputs:" && echo "Expected: Input1: 2.99802 3.03753, Input2: 1.9406 8.00725, Input3: 1.59266 8.63027, Input4: 3.62952 15.1485" && echo "" && for i in 1 2 3 4; do printf "Input$i: "; time (cat src/inputs/input$i.md | sed 's/```//' | grep -v '^$' | ./target/release/particle-filter) 2>&1; done
```
