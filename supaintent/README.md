# SupaIntent vids

TikTok-ролики 30 с для SupaIntent (видимость брендов в ChatGPT / AI-поиске). Перенесено из `~/Desktop/SI/Sitt` 22.11.2026.

## Где что
| Что | Где |
|---|---|
| Код, сценарии (`SCRIPT.md`, `*.json`), шрифты, лого, скриншоты, персонажи | этот каталог (git) |
| Ключи | `.env` в корне репо: `GEMINI_API_KEY` (api/align/omni), `OPENAI_API_KEY` (oai) |
| Медиа | Google Drive `My Drive/Projects/TT30/supaintent`: `01_ready/<папка>.mp4` (финалы), `03_work/` (раскладка как здесь) |
| Не видео: `hotleads/` (LinkedIn-лиды, Bright Data) и `агентства/` | только Drive `TT30/supaintent/` |
| Real-ESRGAN для `upscale.sh` | общий `../3d/tools/realesrgan` |

## Форматы
| Папка | Формат | Запуск |
|---|---|---|
| `<тема>/` (chatgpt-ads, fanout, ten-weeks…) | Скриншоты + лого + голос Gemini TTS, музыка Lyria, караоке-субтитры | `python3 vo.py` → `uv run build.py` → `out/final.mp4` |
| `dana*/`, `salesmate/`, `search-trio/` | Анимированный персонаж (Omni 360p + Real-ESRGAN) + вставки скриншотов, OpenAI TTS | `uv run build.py` (докстринг) |
| `stage3d/` | 3D-сцена на three.js в headless Chrome, вырезки gpt-image | `bun install` → `uv run py/art.py videos/<id>` → `bun render.ts <id>` → `uv run --with pillow python py/finish.py <id>` |

Каждая тематическая папка — самостоятельная копия пайплайна (`api.py`, `align.py`, `captions.py`, `vo.py`, `build.py`), бюджет-кэп через `AD_BUDGET_LEFT`.
