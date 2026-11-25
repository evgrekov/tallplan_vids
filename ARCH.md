# TallPlan vids — архитектура

Генерация коротких роликов и слайдов для TallPlan (iOS «Grow Taller — Height Predictor & Growth Plan») под TikTok / Shorts / Google App Campaigns. Перенесено из `~/Desktop/go_tall_tiktok` 21.11.2026.

## Где что хранится
| Что | Где |
|---|---|
| Код пайплайнов, промпты, спеки (`*.json`), отчёты QA, правила | этот репозиторий |
| Ключи | `.env` в корне (в git не попадает): `GEMINI_API_KEY`, `OPENAI_API_KEY`, `FAL_KEY`, `OPENROUTER_API_KEY`, `BRIGHTDATA_API` (Bright Data, Bearer-токен для `api.brightdata.com`: Datasets / Web Scraper API — парсеры и статистика) |
| Статистика | `stats/` (старый аккаунт @go_.tall: `tiktok_go_tall.md`; наши аккаунты: `stats/ours/`; чужие каналы: `stats/refs/<handle>/`) + `top10/` (разбор слайдов топ-10 постов) |
| Общая таблица фермы | Google Sheet «TT farm accounts», id `1XfssHqNvfstrUMoLvSEWP0U-q4wvFnnTapwADjAJu-M` (см. ниже) |
| Выводы по референсам | `research/INSIGHTS.md` |
| Медиа | Google Drive `My Drive/Projects/TT30/tallplan` ([TT30](https://drive.google.com/drive/folders/1l4HFp1fJXSZIwr82rDOz29jwjxJiGLRE), [tallplan](https://drive.google.com/drive/folders/1C7IKWNLZWZpoxw-gmmiZOg7-sk8jsMNu)): `01_ready/<tt№>_<handle>/` (по аккаунтам; старое в `01_ready/_archive/`), `02_sources/` (бренд, референсы, топ-10), `03_work/` (раскладка как в репо), `04_assets/` (официальные материалы TallPlan: экраны и записи экрана в `Screenshots/iOS/promo/{ft,cm}`, ASO для App Store и Google Play, логотипы; каталог — вкладка `Assets`). Индекс роликов — `DRIVE.md` |
| brand-ассеты, которые читают скрипты (лого, скриншоты, `man.png`, `packshot.png`, шрифты) | и в репо, и на Drive |
| Real-ESRGAN (`3d/tools/realesrgan`, 70 МБ) | только локально в репо (gitignored); при потере — скачать ncnn-vulkan сборку с github.com/xinntao/Real-ESRGAN |

Новые генерации пишутся в папки репо (медиа там игнорируется git), дальше раскладываем на Drive по правилу из `DRIVE.md`.

## Общие правила (для всех форматов)
- **Перед любой новой генерацией сверяемся с вкладками `Rules*` общей таблицы** (шаблон канала → общие правила → активные тренды), ID применённых правил пишем в спеку и в `Vids.notes`. Новые выводы из `research/INSIGHTS.md` переносим туда же.
- **Нейросети только свои ключи:** Google (Gemini — анализ, планы, QA, TTS, видео omni, музыка Lyria) и OpenAI (картинки gpt-image, озвучка). Озвучка OpenAI — только `slides/oai.speech` → `slides/say_rt.py` на `gpt-realtime-2.1-mini` (Realtime API; Speech API модели `gpt-4o-mini-tts`/`tts-1` отключают 6.01.2027). Голос по умолчанию `cedar`, бодрость задаёт текст стиля, а не speed (speed ≠ 1 — ffmpeg atempo); модель сверяет транскрипт с текстом и переделывает перефраз. fal — только `gen/`. Higgsfield/ElevenLabs не используем.
- **Видео-генерация — самый дорогой шаг.** Сначала собираем из уже сгенерированного футажа (Drive `03_work`): новый голос, картинки, подписи дешёвые.
- **Всегда считаем и пишем итоговую стоимость** (с разбивкой Google / OpenAI). Бюджет-кэп на ролик в `3d/auto.py` — $2.
- **Распознаём референс, а не выдумываем:** Gemini разбирает референс (кадры, голос, субтитры) → план → генерация.
- **Нейросеть не рисует текст.** Субтитры, подписи, пэкшот — всегда в монтаже (Pillow + ffmpeg).
- **Бренды и известные вещи — настоящие материалы.** Упоминаем бренд, компанию, игру, фильм, историю (GTA 6, McDonald's…) — ищем в интернете их настоящие фото, логотипы, кадры и видео (лучше официальные/пресс-кит), кладём в Drive `02_sources/brands/<бренд>/` с ссылкой на источник и вставляем в монтаж. Один текст — слишком бедно. Нейросеть логотипы не рисует; не подаём как рекламу от бренда; конкурентов (приложения про рост) не показываем. Правило G23 в `RulesGlobal`.
- **Хук** — вопрос про самого зрителя / его тело, ≤4 слов в подписи; упражнение в кадре с первого кадра, без заставок.
- **Безопасные зоны:** подписи ≥270 px сверху, ничего важного ниже 0.76H, текст ≤80% ширины.
- **Финал:** пэкшот TallPlan + «PREDICT / YOUR HEIGHT», стартует на CTA-фразе.
- **Формулировки мягкие:** осанка, спина, гибкость, «стоять выше». Никаких гормонов, плотности костей, гарантий роста, сравнений тел, названий конкурентов.
- **Персонаж — взрослый 19–20 лет**, одет (несовершеннолетних фотореал блокирует модерация).
- **Шаги идемпотентны:** удалил файл — шаг пересоздастся.
- **QA-гейт перед каждым платным шагом**, максимум 2 перегенерации, потом стоп и отчёт.

## Форматы и пайплайны
| Папка | Формат | Запуск | Цена | Подробно |
|---|---|---|---|---|
| `3d/` | Ремейк референса: 3D-аниме-персонаж, голос, SFX, музыка, караоке-субтитры | `python3 auto.py <url> <folder>` | ~$0.2–1 | `3d/rules.md`, `3d/storyboard*.md`, `3d/pipeline/prompts/` |
| `muscle/` | 3D-манекен делает упражнение, рабочая мышца светится, карусель иконок. **Ремикс** (`f1_*`): новая папка с reel.json, клипы/стиллы/музыка копируются из старых папок с Drive → `gen.py` делает только голос (~$0.005) | `uv run gen.py <x>/reel.json` → `render_overlay.py` → `assemble.py` | — | `muscle/README.md`, скилл `muscle-reel` |
| `slides/make.py` | Слайдшоу упражнений без голоса, нарезка по биту | `uv run make.py <url> <folder> "<style>" ["<brief>"]` | ~$0.23 | `slides/README.md` |
| `slides/myth.py` | Миф → факт, 2 слайда | | | `slides/README.md` |
| `slides/stopmo.py` | stop-motion: бумажные вырезки, рука, голос | | ~$0.44 | `slides/README.md` |
| `slides/char.py` | mascot cut-out анимация, сюжет по брифу | | ~$0.8 | `slides/README.md`, `slides/FORMATS.md` |
| `slides/facts.py` | facts: векторный персонаж + линейка роста | | ~$0.7 | `slides/README.md` |
| `slides/grid.py` | Сетка 2×2 «glow up» | `uv run grid.py grid/<spec>.json` | ~$0.24 | `slides/FORMATS.md` |
| `slides/quiz.py` | UGC-квиз: фото + таблица/коммент → экраны квиза → реальный экран TallPlan | `uv run quiz.py quiz/<spec>.json` | ~$0.07 | `slides/FORMATS.md` |
| `table/table.py` | Reveal table (@todd.f.moir): лист-таблица, бумага открывает по строке под голос, «YOU ??» → коммент, ответ — реальный экран прогноза TallPlan, потом пэкшот. Без видео | `uv run table.py <x>/spec.json` | ~$0.01 | докстринг |
| `family/family.py` | Ответ на комментарий (@how.tall.will.i.b, C-HTW): карточка коммента, кривые фигурки семьи на шкале роста по одной на фразу, формула (папа + мама ± 5) ÷ 2 с жёлтым результатом, карточка прогноза TallPlan, утешение + CTA, пэкшот. Без видео | `uv run family.py <x>/spec.json` | ~$0.015 | докстринг |
| `path/path.py` | Final height X по годам (@staturesecrets, C-STAT): чёрная линейка, наш лаймовый персонаж растёт с 12 до 18 лет (% от взрослого роста, CDC), серые призраки прошлых лет, финишная линия, карточка-угол (страны / формула родителей), «genes set your range», карточка TallPlan, slowed phonk из референса под голосом. Сценарий общий, спека задаёт только рост и угол | `uv run path.py <x>/spec.json` | ~$0.02 | докстринг |
| `selfie/selfie.py` | Селфи + таблица роста (@heightible, @gotall.abdul, C-SELF): готовое селфи из прошлых генераций, медленный наезд, «If you're N and X → ~Y at 18» над лицом с первого кадра, громкий звук из референса, без голоса, карточка TallPlan на последних 2 с, ≤12 с | `uv run selfie.py <x>/spec.json` (рядом `photo.png`) | $0 | докстринг |
| `slides/kit.py` | Общее для family/ и path/: шрифт, кривая фигурка-капсула, карточка прогноза TallPlan, TTS-строки, сборка ffmpeg из полноэкранных состояний | — | — | докстринг |
| `gads/` | Google App Campaigns: сцены-экраны телефона, 9:16 / 1:1 / 16:9 | `uv run gads/<name>.py` | — | докстринги в `gads/*.py` |
| `gen/` | Пересборка слайдов топ-10 постов (fal, gpt-image) по разбору `top10/` | `python3 gen/build.py <NN>` / `gen/full.py` | — | код |
| `yt_remake/` | Перезвучка готовых 3d-роликов новым голосом OpenAI без перегенерации видео | `python3 remake3d.py <3d/adN> <sfx.mp4> <out>` | — | докстринг |
| `supaintent/` | **Другой проект — SupaIntent:** TikTok 30 с про видимость брендов в ChatGPT (скриншоты, персонаж Dana, 3D-сцена `stage3d`). Медиа — Drive `TT30/supaintent` | см. README | — | `supaintent/README.md` |

## TikTok-ферма: кто что делает
- **Мы (этот репо):** генерируем ролики, собираем статистику своих и чужих аккаунтов, исследуем референсы.
- **Агент друга (вне репо, со своими доступами):** постит ролики по аккаунтам и сам выбирает время.
- Связь — общая таблица. Вкладки:

| Вкладка | Чья | Что |
|---|---|---|
| `README` | общая | инструкция по ролям: что делает генерация, что публикация, статусы |
| `Vids` | общая | очередь и опубликованные ролики. Мы: handle, duration_s, description, sound, notes, статистика, `status=queue`. Публикация: url, post_id, posted, `status` (posted / problem / skipped / removed), `publisher_notes` (сбои, наблюдения). При сборе статистики читаем `publisher_notes` |
| `Stats` | наша | журнал снимков статистики по роликам (дата снимка, `kind`: `ref` — чужие); формулы ER и возраста |
| `ChannelStats` | наша | снимки по каналам: подписчики, видео, медиана/максимум просмотров |
| `Accounts` | друга | аккаунты фермы. **Колонку паролей не читаем и не используем** |
| `WarmupLog` | друга | прогрев аккаунтов |
| `Refs` | наша | чужие каналы-референсы: формат, персонаж, почему интересен; цифры — формулами из `ChannelStats` |
| `RefVids` | наша | разбор чужих роликов, 75 колонок по слоям (id / stats / what / feel / craft / sound / insight / files); stats — формулами из `Stats` |
| `Music` | наша | звуки из роликов: голос/музыка, где использован, лучшие просмотры (формулы из `RefVids`) |
| `Codebook` | наша | словарь колонок `RefVids`: смысл и допустимые значения |
| `Rules` | наша | порядок сверки перед генерацией и уровни правил |
| `RulesGlobal` | наша | общие правила роликов (G01…), с доказательствами |
| `RulesChannels` | наша | правила шаблонов каналов, которые повторяем (C-TODD, C-HTW, C-STAT…) |
| `RulesTrends` | наша | актуальные темы с датами активности и правилом подмеса (T-XMAS, T-GTA6…) |
| `Assets` | наша | каталог `04_assets`: какой экран или запись что показывает, какие цифры в кадре, когда брать (правила G24–G29) |

Схема колонок и все формулы — в `research/schema.py` (`python3 research/schema.py headers|codebook|cols`); строки собираем через него, не руками. 19-значные id пишем с апострофом (`'7708…`), иначе Sheets округлит.

## Исследование референсов (`research/`)
Статистику и разборы собираем **только когда пользователь просит**. Сейчас фаза исследования: собираем механики, сценарии и ролики не предлагаем, пока не попросят.

| Шаг | Команда | Результат |
|---|---|---|
| Профиль канала | `python3 research/ref.py profile <handle>` | `stats/refs/<handle>/<дата>_profile.json` |
| Посты канала | `python3 research/ref.py posts <handle> [n]` | `stats/refs/<handle>/<дата>_posts.json` |
| Сводка канала | `python3 research/channel.py <handle> [top]` | медиана, топ постов, ER, сохранения (нужны оба файла выше) |
| Разбор ролика | `python3 research/ref.py video <url>` | видео → Drive `02_sources/references/tiktok/<handle>/<views>_<id>.mp4`, звук → `02_sources/music/` (если посты уже скачаны), кадры `sheet.png`/`hook.png`, склейки, речь (локальный Whisper) → `research/work/<handle>/<id>/summary.json` (gitignored) |
| Карусель | `python3 research/ref.py photo <url>` | слайды + звук на Drive |
| Комментарии | `python3 research/ref.py comments <url>` | `stats/refs/<handle>/<дата>_comments_<id>.json` |

Bright Data Datasets v3 (ключ `BRIGHTDATA_API`): profile `gd_l1villgoiiidt09ci`, posts `gd_lu702nij2f790tmv9h` (discover_by=profile_url), comments `gd_lkf2st302ap89utw5k`. Платного AI в разборе нет: кадры и транскрипт смотрим сами.

Порядок разбора канала: profile + posts → `channel.py` → `video` для топ-5 и 1 провального для контраста → (по желанию) `comments` топ-2 → строки в `Stats`, `RefVids`, `ChannelStats`, `Refs`, `Music` → персонаж в Drive `02_sources/characters/<slug>/` (кадры + `character.md`) → раздел в `research/INSIGHTS.md` (таблица постов, «что работает», идеи 🟢/🟡). Whisper на роликах без голоса выдаёт мусор («Music», «FADE OUT») — тогда транскрипт пустой, `voice` = none.

## Ключевые выученные уроки (3d)
- Видео — `gemini-omni-1.1-flash` только через Interactions API, ≤10 с за генерацию, дальше extend (+8 с). Лимит Tier 1: 20 видео-запросов/сутки.
- Генерим 360p (в ~3 раза дешевле) → локальный апскейл Real-ESRGAN x2 → 60 fps.
- Voice-first: TTS задаёт таймкоды, видео генерит только SFX, Lyria — музыку.
- Тайминги слов Gemini дрейфуют до 1 с — субтитры выравниваем по огибающей голоса (`align.py`).
- Ключевой кадр на каждую позу (gemini image) решает позы и анатомию; крупные планы тела как вход ловят safety-фильтр.
- Гарды промптов: CHARACTER LOCK, CLEAN FRAME, ANATOMY LOCK — см. `3d/rules.md`.

## Что заходит (статистика)
Подробно: `stats/tiktok_go_tall.md`. Коротко: 83 поста, 676 тыс. просмотров; топ-2 (161 тыс. и 53 тыс.) — карусели про упражнения с аномально высокими сохранениями → «полезное, сохраню».
