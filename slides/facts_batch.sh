#!/bin/zsh
# Batch 2026-11-27: five facts explainers for the YouTube Tallplan channel (same face: sheet.png of facts1, one saved sound each).
cd "${0:A:h}"
REF=https://youtube.com/shorts/y6Gz5uQafsM  # unused when reference.mp4 is already in the folder
run() { uv run facts.py $REF "$@" > "$1.log" 2>&1 && echo "✅ $1" || echo "❌ $1 (see $1.log)"; }

run facts5 "Sleep and height: why teens need more sleep" \
  "Teens need 8 to 10 hours of sleep a night. About 7 in 10 US high schoolers sleep less than 8 hours on school nights. The body does most of its repair and growth work during deep sleep at night. Screens right before bed can delay falling asleep. A regular bedtime helps you reach your natural height; sleep cannot take you past what your genes allow." \
  7604889772407719952 &
run facts6 "Posture: how many inches slouching hides" \
  "Slouching can make you look 1 to 2 inches shorter than you really are. Looking down at a phone pushes the head forward and strains the neck more the lower you bend. Standing tall means ears over shoulders and shoulders over hips. Core and back exercises make good posture easier to hold. Good posture shows your full height, it does not make bones longer." \
  7678389289608136705 &
run facts7 "Your parents' height and how tall you will be" \
  "Genes explain about 80% of the differences in height between people. Doctors estimate adult height from the parents: for a boy, mom's height plus dad's height plus 5 inches, divided by 2; for a girl, the same minus 5 inches. Example: mom 5'4\", dad 5'10\" gives a son about 5'9.5\" and a daughter about 5'4.5\". The real adult height usually lands within about 4 inches of that estimate. Sleep, food and activity decide where in that range you end up." \
  7615235308002936848 &
run facts8 "Will you be taller by next Christmas? (Christmas wrapper: labels like 'Christmas 2026' / 'Christmas 2027', a Christmas tree or gift icon)" \
  "At the peak of the growth spurt girls grow about 3 inches a year, usually around age 11 to 12. Boys grow about 3.5 to 4 inches a year at their peak, usually around age 13 to 14. Kids and teens tend to grow faster in spring and summer than in fall and winter. Boys usually keep growing about 2 years longer than girls. So between this Christmas and the next, a teen in a growth spurt can add several inches." \
  7023195722158491649 &
run facts9 "Hands and feet grow first: early signs of a growth spurt" \
  "Hands and feet are the first parts of the body to speed up in a growth spurt, before the legs and the spine. Suddenly needing bigger shoes can be an early sign a growth spurt is starting. Feet usually stop growing a couple of years before your height does. Shoe size alone cannot predict your final height. Your arm span, fingertip to fingertip, is roughly equal to your height." \
  7593401998129776656 &
wait
