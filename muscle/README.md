# Muscle reel: отдельный формат креатива

Формат «3D-манекен делает упражнение, рабочая мышца светится». Основа: скилл muscle-reel по образцу @joinyoucan, у которого 4–9 млн просмотров.
Внешние сервисы заменены на наши.

| Что | Чем | Счёт |
|---|---|---|
| Кадры и иконки | OpenAI images (`oai.edit` по двум style-ref, `oai.image`) | OpenAI |
| Анимация клипов | `3d/omni.py` (gemini-omni-1.1-flash, 720p, старт с кадра) | Google |
| Голос | OpenAI TTS | OpenAI |
| Музыка | Lyria 3 Pro (~60 s) | Google |

## Тайминг
- ~4.5 s: интро.
- Затем 5 секций примерно по 10.5 s, в каждой 2 клипа.
- Сверху стеклянная плашка: карусель иконок мышц, неоновая рамка цвета мышцы, название появляется под голос.
- Под фразу tagline идёт наш пэкшот + «PREDICT / YOUR HEIGHT».
- Плашка опущена на 150 px относительно оригинала: название на y≈296, ниже TikTok-зоны 270 px.

## Запуск
```
uv run gen.py posture/reel.json             # кадры, иконки, клипы, голос, музыка (идемпотентно)
uv run render_overlay.py posture/reel.json  # UI-оверлей PNG
uv run assemble.py posture/reel.json        # сборка + пэкшот → posture/final.mp4
```

## Файлы
- `style.txt`: общий STYLE-блок кадров. Манекен без гантелей, верхние 35% кадра пустые под плашку.
- `posture/reel.json`: TallPlan-версия.
  - Секции: Upper back, Core, Glutes, Hamstrings, Spine.
  - У каждого клипа: `shot` (кадр), `move` (движение), `camera`, `dur`.
  - Также в файле: скрипт голоса, голос, музыка.
- Новая версия = новая папка с reel.json, `sections` меняются.
- Цвета мышц:
  - Upper back бирюзовый
  - Core красный
  - Glutes розовый
  - Hamstrings синий
  - Spine жёлтый
- `assets/`: style-ref кадры и шрифт Archivo (OFL) из скилла.
