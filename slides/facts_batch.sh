#!/bin/zsh
# Batch 2026-11-27 #2: facts10-14 for the YouTube Tallplan channel. Same face (face.png = facts1 sheet), each video its own look + saved sound.
cd "${0:A:h}"
DRIVE="$HOME/Library/CloudStorage/GoogleDrive-evgrekov@gmail.com/My Drive/Projects/TT30/tallplan"
run() {
  mkdir -p $1
  [[ -f $1/reference.mp4 ]] || cp "$DRIVE/02_sources/references/slides_facts1.mp4" $1/reference.mp4
  [[ -f $1/face.png ]] || cp "$DRIVE/03_work/slides/facts1/sheet.png" $1/face.png
  uv run facts.py x "$@" > "$1.log" 2>&1 && echo "✅ $1" || echo "❌ $1 (see $1.log)"
}

run facts10 "Does basketball make you taller?" \
  "The average NBA player is about 6'6\" tall. Basketball does not make bones grow longer: tall people are picked for basketball, not made by it. Regular exercise supports healthy bones, muscles and posture while you grow. Jumping and running sports help build strong bones in the teen years. Any sport you enjoy is good for growing up healthy; none of them can take you past your genetic height." \
  7478723169449658369 "Warm peach and coral palette (backgrounds like #ffd9c2 and #ff9f7a); soft flat vector illustration with a subtle grainy texture and gentle shading" &
run facts11 "What to eat to reach your natural height" \
  "Teens need about 1,300 mg of calcium a day, more than adults. Vitamin D helps the body absorb that calcium; sunlight and foods like milk, eggs and fish give it. Protein is the building block for muscles and growing tissue. Kids who do not get enough food overall can end up shorter than their genes allow. Eating more than you need does not make you taller than your genes allow." \
  7443847444193282064 "Fresh mint and teal palette (backgrounds like #c9f2e3 and #5fd3bd); clean semi-flat vector with soft gradients and a light rim light" &
run facts12 "Late bloomers: why some teens grow later" \
  "Puberty can normally start anywhere from about 8 to 13 for girls and 9 to 14 for boys. Late bloomers start their growth spurt later than their friends. Many late bloomers keep growing after their friends have stopped and catch up. Being the shortest in your class at 13 says little about your adult height. Doctors check growth over time, not one measurement." \
  7666848422541363238 "Soft lavender and violet palette (backgrounds like #e3d9ff and #a99bff); rounded cute flat illustration with big friendly shapes and soft shadows" &
run facts13 "Does coffee stunt your growth?" \
  "The idea that coffee stunts growth is a myth: studies have not found that coffee makes people shorter. The real problem is sleep: caffeine can stay in the body for 5 hours or more. Caffeine late in the day can make it harder to fall asleep and sleep deeply. Teens need 8 to 10 hours of sleep a night. Experts advise teens to keep caffeine low, at most about 100 mg a day, roughly one cup of coffee." \
  7298748072409942018 "Sunny yellow and warm orange palette (backgrounds like #ffeb99 and #ffc857); bold flat comic-style illustration with clean thick dark outlines" &
run facts14 "Growth charts: are you on track?" \
  "Doctors compare your height with growth charts for your age and sex. At 14 the average boy in the US is about 5'4.5\" and the average girl about 5'3\". Percentiles show how you compare: the 50th percentile means half of kids your age are taller and half shorter. What matters most is that you keep growing along your own curve over time. A sudden drop across percentile lines is a reason to talk to a doctor." \
  7457203853475235857 "Pastel sky blue and soft pink palette (backgrounds like #d4ebff and #ffcfe3); paper cut-out collage illustration with a subtle paper texture and soft drop shadows" &
wait
