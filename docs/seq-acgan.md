# Seq-ACGAN

`SequenceGenerator` получает гауссов шум на каждом временном шаге и условную
метку (`normal` или `anomaly`), затем GRU генерирует 14-дневный векторный ряд.
`SequenceDiscriminator` — двунаправленный GRU с общим embedding и двумя
отдельными выходами:

1. `source_head`: настоящая или синтетическая последовательность;
2. `anomaly_head`: нормальное или аномальное поведение.

Дискриминатор минимизирует source loss для настоящих и искусственных данных и
classification loss для обоих типов. Генератор одновременно стремится быть
распознанным как настоящий и соответствовать запрошенному классу.

Для борьбы с редкостью аномалий DataLoader балансирует классы с возвращением,
но **не добавляет** validation/test в обучение.

```powershell
# Проверка контура на CPU
$env:PYTHONPATH = 'src'
python scripts/train_seq_acgan.py --smoke-test

# Полный первый прогон
$env:PYTHONPATH = 'src'
python scripts/train_seq_acgan.py --epochs 40 --max-normal 30000
```

Для r4.2 используется устойчивый контур `train_stable_seq_acgan.py`: bounded
log-transform, `tanh` на выходе генератора, LayerNorm, spectral normalization
и feature matching.
