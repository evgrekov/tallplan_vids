# Google Drive: TT30/src

`My Drive/Projects/TT30/src`:
- `01_ready/<формат>/` — финальные ролики: `<папка>_<тема>[_вариант].mp4`
- `02_sources/` — `brand/` (киты, мокапы), `references/` (`<формат>_<папка>.mp4` + `.info.json` с исходной ссылкой, `youtube/`), `our-top10-posts/`
- `03_work/` — кадры, клипы, голос, музыка, черновики; раскладка как в репо (`3d/ad4/` ↔ `03_work/3d/ad4/`)
- `02_sources/references/tiktok/<handle>/<views>_<post_id>.mp4` — чужие топ-ролики (Refs / RefVids в таблице)
- `02_sources/characters/<slug>/` — коллекция персонажей из чужих роликов: кадры `NN_<ракурс>_<поза>.png` (полный рост, профиль, лицо, ключевые позы), `00_sheet.png`, `character.md` (источник, описание, набросок промпта для генерации похожего)
- `02_sources/music/<sound_id>_<title>.m4a` — звуки из роликов (вкладка Music: использование, просмотры, лучшие ролики)

Новый ролик: генерируем в папке репо → финал в `01_ready/<формат>/`, референс в `02_sources/references/`, остальное в `03_work/<та же папка>`.

## Готовые ролики
| Файл | Формат | Тема | Рабочая папка |
|---|---|---|---|
| `3d-remakes/ad02.mp4` | 3d remake | ad02 | `3d/ad2` |
| `3d-remakes/ad02_anime.mp4` | 3d remake | ad02 | `3d/ad2` |
| `3d-remakes/ad03_signs-you-stopped-growing-remake.mp4` | 3d remake | Signs You Stopped Growing - TallPlan Remake | `3d/ad3` |
| `3d-remakes/ad3_tts_signs-you-stopped-growing-remake.mp4` | 3d remake | Signs You Stopped Growing - TallPlan Remake | `3d/ad3_tts` |
| `3d-remakes/ad3_v01_signs-you-stopped-growing-remake.mp4` | 3d remake | Signs You Stopped Growing Remake | `3d/ad3_v1` |
| `3d-remakes/ad3_v02_mythbust-ab-hair-growth-check.mp4` | 3d remake | TallPlan Mythbust - Ab Hair & Growth Check | `3d/ad3_v2` |
| `3d-remakes/ad04_adam-s-apple-height-predictor.mp4` | 3d remake | TallPlan Adam's Apple Height Predictor | `3d/ad4` |
| `3d-remakes/ad05_optimal-sleeping-alignment-for-height.mp4` | 3d remake | Optimal Sleeping Alignment for Height | `3d/ad5` |
| `3d-remakes/ad5_v01_sleep-posture-height-growth.mp4` | 3d remake | Sleep Posture Height Growth | `3d/ad5_v1` |
| `3d-remakes/ad06_essential-growth-stretches.mp4` | 3d remake | Essential Growth Stretches | `3d/ad6` |
| `3d-remakes/ad07_4-way-growth-matrix-routine.mp4` | 3d remake | 4-Way Growth Matrix Routine | `3d/ad7` |
| `3d-remakes/ad7_grid.mp4` | 3d remake | ad7 grid | `3d/ad7_grid` |
| `3d-remakes/ad7_grid_2.mp4` | 3d remake | ad7 grid | `3d/ad7_grid` |
| `3d-remakes/ad7_grid_3.mp4` | 3d remake | ad7 grid | `3d/ad7_grid` |
| `3d-remakes/wall-camel-stretch_long_720.mp4` | 3d remake (manual) | Wall camel stretch | `3d` |
| `3d-remakes/wall-camel-stretch_long_720v2.mp4` | 3d remake (manual) | Wall camel stretch | `3d` |
| `3d-remakes/wall-camel-stretch_long_v2.mp4` | 3d remake (manual) | Wall camel stretch | `3d` |
| `3d-remakes/wall-camel-stretch_long_v3.mp4` | 3d remake (manual) | Wall camel stretch | `3d` |
| `3d-remakes/wall-camel-stretch_long_v4.mp4` | 3d remake (manual) | Wall camel stretch | `3d` |
| `3d-remakes/wall-camel-stretch_test_5s_v3.mp4` | 3d remake (manual) | Wall camel stretch | `3d` |
| `google-ads/googling_16x9.mp4` | Google App campaign | googling | `gads/googling` |
| `google-ads/googling_1x1.mp4` | Google App campaign | googling | `gads/googling` |
| `google-ads/googling_9x16.mp4` | Google App campaign | googling | `gads/googling` |
| `google-ads/groupchat_16x9.mp4` | Google App campaign | groupchat | `gads/groupchat` |
| `google-ads/groupchat_1x1.mp4` | Google App campaign | groupchat | `gads/groupchat` |
| `google-ads/groupchat_9x16.mp4` | Google App campaign | groupchat | `gads/groupchat` |
| `muscle-reels/dumb.mp4` | muscle reel | dumb | `muscle/dumb` |
| `muscle-reels/dumb_full.mp4` | muscle reel | dumb | `muscle/dumb` |
| `muscle-reels/dumb02.mp4` | muscle reel | dumb02 | `muscle/dumb2` |
| `muscle-reels/dumb02_full.mp4` | muscle reel | dumb02 | `muscle/dumb2` |
| `muscle-reels/dumb03.mp4` | muscle reel | dumb03 | `muscle/dumb3` |
| `muscle-reels/dumb03_full.mp4` | muscle reel | dumb03 | `muscle/dumb3` |
| `muscle-reels/hips.mp4` | muscle reel | hips | `muscle/hips` |
| `muscle-reels/neck.mp4` | muscle reel | neck | `muscle/neck` |
| `muscle-reels/sleep.mp4` | muscle reel | sleep | `muscle/sleep` |
| `muscle-reels/test.mp4` | muscle reel | test | `muscle/test` |
| `muscle-reels/upback.mp4` | muscle reel | upback | `muscle/upback` |
| `mascot/char01_unlock-your-full-height-with-rulo.mp4` | mascot cut-out | Unlock Your Full Height with Rulo | `slides/char1` |
| `mascot/char02_shrimpy-s-guide-to-standing-taller.mp4` | mascot cut-out | Shrimpy's Guide to Standing Taller | `slides/char2` |
| `mascot/char03_can-you-actually-grow-taller.mp4` | mascot cut-out | Can You Actually Grow Taller? | `slides/char3` |
| `mascot/char04_sprouty-s-secret-to-growing-tall.mp4` | mascot cut-out | Sprouty's Secret to Growing Tall | `slides/char4` |
| `mascot/char05_how-gerry-reached-the-top-leaves.mp4` | mascot cut-out | How Gerry Reached the Top Leaves | `slides/char5` |
| `mascot/char06_signs-you-re-still-growing.mp4` | mascot cut-out | Signs You're Still Growing | `slides/char6` |
| `mascot/char07_signs-a-growth-spurt-is-coming.mp4` | mascot cut-out | Signs a Growth Spurt is Coming | `slides/char7` |
| `mascot/char08_signs-your-posture-is-stealing-your-height.mp4` | mascot cut-out | Signs Your Posture Is Stealing Your Height | `slides/char8` |
| `exercise-slides/ex01_rounded-shoulders-phone-fix.mp4` | exercise slides | Rounded Shoulders Phone Fix | `slides/ex1` |
| `exercise-slides/ex10_want-to-stand-taller-upper-back.mp4` | exercise slides | Want To Stand Taller? Upper Back | `slides/ex10` |
| `exercise-slides/ex02_back-stiff-after-school.mp4` | exercise slides | Back Stiff After School? | `slides/ex2` |
| `exercise-slides/ex03_spine-decompression-shorts-ad.mp4` | exercise slides | TallPlan Spine Decompression Shorts Ad | `slides/ex3` |
| `exercise-slides/ex04_head-pokes-forward-two-move-posture-reset.mp4` | exercise slides | Head Pokes Forward? Two-Move Posture Reset | `slides/ex4` |
| `exercise-slides/ex05_sitting-all-day-hip-reset.mp4` | exercise slides | Sitting All Day Hip Reset | `slides/ex5` |
| `exercise-slides/ex06_2-minute-morning-posture-routine.mp4` | exercise slides | 2-Minute Morning Posture Routine | `slides/ex6` |
| `exercise-slides/ex07_before-bed-spine-relax.mp4` | exercise slides | Before-Bed Spine Relax | `slides/ex7` |
| `exercise-slides/ex08_always-slouching-core-posture-fix.mp4` | exercise slides | Always Slouching? Core Posture Fix | `slides/ex8` |
| `exercise-slides/ex09_can-t-touch-your-toes-hamstring-reset.mp4` | exercise slides | Can't Touch Your Toes? Hamstring Reset | `slides/ex9` |
| `facts/facts01_when-do-you-actually-stop-growing.mp4` | facts explainer | When Do You Actually Stop Growing? | `slides/facts1` |
| `facts/facts02_how-human-height-changed-around-the-world.mp4` | facts explainer | How Human Height Changed Around the World | `slides/facts2` |
| `facts/facts03_why-your-height-changes-every-day.mp4` | facts explainer | Why Your Height Changes Every Day | `slides/facts3` |
| `facts/facts04_how-fast-do-humans-actually-grow.mp4` | facts explainer | How Fast Do Humans Actually Grow? | `slides/facts4` |
| `form-fixes/fx01_plank-fix-dead-bug.mp4` | wrong vs right form | Plank Fix + Dead Bug | `slides/fx1` |
| `form-fixes/fx10_hamstring-stretch-mistake-fix.mp4` | wrong vs right form | Hamstring Stretch Mistake Fix | `slides/fx10` |
| `form-fixes/fx02_dead-hang-fix-for-taller-posture.mp4` | wrong vs right form | Dead Hang Fix for Taller Posture | `slides/fx2` |
| `form-fixes/fx03_wall-angels-you-re-wrong.mp4` | wrong vs right form | Wall Angels: You're Wrong | `slides/fx3` |
| `form-fixes/fx04_cobra-stretch-fix.mp4` | wrong vs right form | Cobra Stretch Fix | `slides/fx4` |
| `form-fixes/fx05_glute-bridge-fix-for-taller-posture.mp4` | wrong vs right form | Glute Bridge Fix for Taller Posture | `slides/fx5` |
| `form-fixes/fx06_forward-fold-fix.mp4` | wrong vs right form | TallPlan Forward Fold Fix | `slides/fx6` |
| `form-fixes/fx07_chin-tucks-you-re-wrong.mp4` | wrong vs right form | Chin Tucks: You're Wrong | `slides/fx7` |
| `form-fixes/fx08_bird-dog-fix-superman-hold.mp4` | wrong vs right form | Bird Dog Fix + Superman Hold | `slides/fx8` |
| `form-fixes/fx09_standing-posture-fix.mp4` | wrong vs right form | Standing Posture Fix | `slides/fx9` |
| `grid-2x2/aura.mp4` | 2x2 grid | aura | `slides/grid/aura` |
| `grid-2x2/glowup.mp4` | 2x2 grid | glowup | `slides/grid/glowup` |
| `grid-2x2/posture.mp4` | 2x2 grid | posture | `slides/grid/posture` |
| `myth-vs-fact/myth01_growth-plates-myth-vs-fact.mp4` | myth vs fact | Growth Plates Myth vs Fact | `slides/myth1` |
| `myth-vs-fact/myth10_18th-birthday-myth-vs-fact.mp4` | myth vs fact | TallPlan - 18th Birthday Myth vs Fact | `slides/myth10` |
| `myth-vs-fact/myth11_phone-neck-myth-vs-fact.mp4` | myth vs fact | Phone Neck Myth vs Fact | `slides/myth11` |
| `myth-vs-fact/myth12_platform-shoes-vs-posture-realignment.mp4` | myth vs fact | Platform Shoes vs Posture Realignment | `slides/myth12` |
| `myth-vs-fact/myth13_myth-vs-fact-daily-habits.mp4` | myth vs fact | TallPlan Myth vs Fact - Daily Habits | `slides/myth13` |
| `myth-vs-fact/myth14_core-muscles-and-height.mp4` | myth vs fact | Core Muscles and Height | `slides/myth14` |
| `myth-vs-fact/myth15_posture-attraction-myth-vs-fact.mp4` | myth vs fact | Posture Attraction Myth vs Fact | `slides/myth15` |
| `myth-vs-fact/myth16_myth-vs-fact-destined-to-stay-small.mp4` | myth vs fact | Myth vs Fact: Destined to Stay Small | `slides/myth16` |
| `myth-vs-fact/myth17_spinal-discs-recovery-myth.mp4` | myth vs fact | Spinal Discs Recovery Myth | `slides/myth17` |
| `myth-vs-fact/myth18_stretching-for-height-myth-debunked.mp4` | myth vs fact | Stretching for Height Myth Debunked | `slides/myth18` |
| `myth-vs-fact/myth19_myth-vs-fact-posture-destiny.mp4` | myth vs fact | TallPlan Myth vs Fact: Posture Destiny | `slides/myth19` |
| `myth-vs-fact/myth02_short-guys-just-accept-it.mp4` | myth vs fact | Short Guys Just Accept It | `slides/myth2` |
| `myth-vs-fact/myth20_pull-up-bar-height-myth.mp4` | myth vs fact | Pull-Up Bar Height Myth | `slides/myth20` |
| `myth-vs-fact/myth03_slouching-vs-height.mp4` | myth vs fact | Slouching vs Height | `slides/myth3` |
| `myth-vs-fact/myth04_myth-vs-fact-stretching.mp4` | myth vs fact | TallPlan Myth vs Fact: Stretching | `slides/myth4` |
| `myth-vs-fact/myth05_daily-height-loss-myth-debunked.mp4` | myth vs fact | Daily Height Loss Myth Debunked | `slides/myth5` |
| `myth-vs-fact/myth06_spine-lengthening-myth-vs-fact.mp4` | myth vs fact | Spine Lengthening Myth vs Fact | `slides/myth6` |
| `myth-vs-fact/myth07_genetics-myth-vs-posture-decompression.mp4` | myth vs fact | Genetics Myth vs Posture Decompression | `slides/myth7` |
| `myth-vs-fact/myth08_sleep-and-height-growth-myth-vs-fact.mp4` | myth vs fact | Sleep and Height Growth Myth vs Fact | `slides/myth8` |
| `myth-vs-fact/myth09_backpack-posture-myth-vs-fact.mp4` | myth vs fact | Backpack Posture Myth vs Fact | `slides/myth9` |
| `quiz/chart.mp4` | UGC quiz | chart | `slides/quiz/chart` |
| `quiz/chart02.mp4` | UGC quiz | chart02 | `slides/quiz/chart2` |
| `quiz/chart03.mp4` | UGC quiz | chart03 | `slides/quiz/chart3` |
| `quiz/comment.mp4` | UGC quiz | comment | `slides/quiz/comment` |
| `quiz/comment02.mp4` | UGC quiz | comment02 | `slides/quiz/comment2` |
| `quiz/comment03.mp4` | UGC quiz | comment03 | `slides/quiz/comment3` |
| `quiz/mom.mp4` | UGC quiz | mom | `slides/quiz/mom` |
| `quiz/mom02.mp4` | UGC quiz | mom02 | `slides/quiz/mom2` |
| `quiz/mom03.mp4` | UGC quiz | mom03 | `slides/quiz/mom3` |
| `slides-from-refs/ref01_height-routine-slideshow.mp4` | slides from reference | TallPlan Height Routine Slideshow | `slides/ref1` |
| `slides-from-refs/ref10_tall-people-do-this.mp4` | slides from reference | Tall People Do This | `slides/ref10` |
| `slides-from-refs/ref11_growth-routine.mp4` | slides from reference | TallPlan Growth Routine | `slides/ref11` |
| `slides-from-refs/ref12_unlock-your-max-height.mp4` | slides from reference | Unlock Your Max Height | `slides/ref12` |
| `slides-from-refs/ref13_ancient-stretches-for-height.mp4` | slides from reference | TallPlan - Ancient Stretches for Height | `slides/ref13` |
| `slides-from-refs/ref14_short-king-to-tall-king.mp4` | slides from reference | Short King to Tall King | `slides/ref14` |
| `slides-from-refs/ref15_5-min-height-routine.mp4` | slides from reference | 5 Min Height Routine | `slides/ref15` |
| `slides-from-refs/ref16_posture-check-height-boost.mp4` | slides from reference | Posture Check Height Boost | `slides/ref16` |
| `slides-from-refs/ref17_before-bed-stretches-for-posture-height.mp4` | slides from reference | Before Bed Stretches for Posture & Height | `slides/ref17` |
| `slides-from-refs/ref18_level-up-your-height-low-poly-3d-workout-plan.mp4` | slides from reference | Level Up Your Height - Low-Poly 3D Workout Plan | `slides/ref18` |
| `slides-from-refs/ref19_look-taller-instantly-routine.mp4` | slides from reference | TallPlan - Look Taller Instantly Routine | `slides/ref19` |
| `slides-from-refs/ref02_height-boost-slideshow.mp4` | slides from reference | TallPlan Height Boost Slideshow | `slides/ref2` |
| `slides-from-refs/ref20_athletes-grow-like-this.mp4` | slides from reference | TallPlan - Athletes Grow Like This | `slides/ref20` |
| `slides-from-refs/ref03_height-routine-slideshow.mp4` | slides from reference | TallPlan Height Routine Slideshow | `slides/ref3` |
| `slides-from-refs/ref04_anime-height-growth-slideshow.mp4` | slides from reference | TallPlan Anime Height Growth Slideshow | `slides/ref4` |
| `slides-from-refs/ref05_growth-stretches-slideshow-ad.mp4` | slides from reference | TallPlan Growth Stretches Slideshow Ad | `slides/ref5` |
| `slides-from-refs/ref06_stop-shrinking-your-spine-routine.mp4` | slides from reference | Stop Shrinking Your Spine Routine | `slides/ref6` |
| `slides-from-refs/ref07_grow-2-inches-by-summer.mp4` | slides from reference | TallPlan - Grow 2 Inches By Summer | `slides/ref7` |
| `slides-from-refs/ref08_morning-height-routine.mp4` | slides from reference | TallPlan Morning Height Routine | `slides/ref8` |
| `slides-from-refs/ref09_posture-height-restoration.mp4` | slides from reference | TallPlan Posture Height Restoration | `slides/ref9` |
| `stop-motion/stopmo01_unlock-your-natural-height-with.mp4` | stop-motion | Unlock Your Natural Height with TallPlan | `slides/stopmo1` |
| `stop-motion/stopmo10_unlock-your-peak-growth-window.mp4` | stop-motion | Unlock Your Peak Growth Window | `slides/stopmo10` |
| `stop-motion/stopmo11_think-you-ve-stopped-growing-check-these-signs.mp4` | stop-motion | Think You've Stopped Growing? Check These Signs | `slides/stopmo11` |
| `stop-motion/stopmo12_why-you-re-taller-in-the-morning.mp4` | stop-motion | Why You're Taller in the Morning | `slides/stopmo12` |
| `stop-motion/stopmo13_sleep-position-height-check.mp4` | stop-motion | Sleep Position Height Check | `slides/stopmo13` |
| `stop-motion/stopmo14_phone-posture-check.mp4` | stop-motion | Phone Posture Check | `slides/stopmo14` |
| `stop-motion/stopmo15_growth-plates-after-18.mp4` | stop-motion | Growth Plates After 18? | `slides/stopmo15` |
| `stop-motion/stopmo16_daily-spine-compression.mp4` | stop-motion | Daily Spine Compression | `slides/stopmo16` |
| `stop-motion/stopmo17_measure-your-height-right.mp4` | stop-motion | Measure Your Height Right | `slides/stopmo17` |
| `stop-motion/stopmo18_one-stretch-before-bed.mp4` | stop-motion | One Stretch Before Bed | `slides/stopmo18` |
| `stop-motion/stopmo19_look-taller-in-10-seconds.mp4` | stop-motion | Look Taller in 10 Seconds | `slides/stopmo19` |
| `stop-motion/stopmo02_why-you-are-shorter-at-night-how-to-fix-it.mp4` | stop-motion | Why You Are Shorter at Night & How to Fix It | `slides/stopmo2` |
| `stop-motion/stopmo20_what-to-eat-for-growing-bones.mp4` | stop-motion | What to Eat for Growing Bones | `slides/stopmo20` |
| `stop-motion/stopmo03_posture-mistakes-stealing-your-height.mp4` | stop-motion | Posture Mistakes Stealing Your Height | `slides/stopmo3` |
| `stop-motion/stopmo04_fix-your-posture-stand-two-inches-taller.mp4` | stop-motion | Fix Your Posture, Stand Two Inches Taller | `slides/stopmo4` |
| `stop-motion/stopmo05_3-night-habits-to-reach-your-natural-height.mp4` | stop-motion | 3 Night Habits to Reach Your Natural Height | `slides/stopmo5` |
| `stop-motion/stopmo06_reclaim-your-hidden-2-inches-with.mp4` | stop-motion | Reclaim Your Hidden 2 Inches with TallPlan | `slides/stopmo6` |
| `stop-motion/stopmo07_why-morning-height-matters.mp4` | stop-motion | Why Morning Height Matters - TallPlan | `slides/stopmo7` |
| `stop-motion/stopmo08_5-minute-height-posture-habit.mp4` | stop-motion | 5-Minute Height & Posture Habit | `slides/stopmo8` |
| `stop-motion/stopmo09_3-posture-fixes-to-stand-3cm-taller.mp4` | stop-motion | TallPlan - 3 Posture Fixes to Stand 3cm Taller | `slides/stopmo9` |
| `yt-revoice/adams_apple.mp4` | re-voiced 3d | adams apple | `yt_remake/adams_apple` |
| `yt-revoice/sleeping_position.mp4` | re-voiced 3d | sleeping position | `yt_remake/sleeping_position` |
| `yt-revoice/stand_taller.mp4` | re-voiced 3d | stand taller | `yt_remake/stand_taller` |
| `yt-revoice/stopped_growing.mp4` | re-voiced 3d | stopped growing | `yt_remake/stopped_growing` |
| `yt-revoice/when_stop_growing_when-do-you-actually-stop-growing.mp4` | re-voiced 3d | When Do You Actually Stop Growing? | `yt_remake/when_stop_growing` |
| `top10-carousel-remakes/post01_2026-05-08_161300views/` | carousel remake of our post | post 01, 161300views | `gen/01` |
| `top10-carousel-remakes/post02_2026-05-02_53300views/` | carousel remake of our post | post 02, 53300views | `gen/02` |
| `top10-carousel-remakes/post03_2026-04-04_46400views/` | carousel remake of our post | post 03, 46400views | `gen/03` |
| `top10-carousel-remakes/post04_2026-04-14_25800views/` | carousel remake of our post | post 04, 25800views | `gen/04` |
| `top10-carousel-remakes/post05_2026-03-30_23400views/` | carousel remake of our post | post 05, 23400views | `gen/05` |
| `top10-carousel-remakes/post06_2026-04-11_17900views/` | carousel remake of our post | post 06, 17900views | `gen/06` |
| `top10-carousel-remakes/post07_2026-03-22_12900views/` | carousel remake of our post | post 07, 12900views | `gen/07` |
| `top10-carousel-remakes/post08_2026-03-28_12800views/` | carousel remake of our post | post 08, 12800views | `gen/08` |
| `top10-carousel-remakes/post09_2026-04-12_12000views/` | carousel remake of our post | post 09, 12000views | `gen/09` |
| `top10-carousel-remakes/post10_2026-06-22_11200views/` | carousel remake of our post | post 10, 11200views | `gen/10` |
