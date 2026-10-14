Beslutningsregel for E5c med sumregel, skrevet 14.10.2026 før 
kjøring på K021-K040

Data: E5c, NorMistral, K021-K040, 3 runder (60 kall), logg 
resultater/e5_pilot/normistral_holdout.jsonl. Ingen omkjøring, 
ingen nye utkast og ingen endring av K etter at resultatet er sett.

Sumregel: scoren er summen av de fire delscorene. Et svar uten alle
fire delscorene teller som mislykket.

NorMistral består hvis alle fire krav holder:
1. Minst 98 % av svarene har alle fire delscorene (høyst 1 av 60 mislykket).
2. Minst 2 av 3 runder er komplette.
3. Hver komplette runde har minst 12 ulike scorer.
4. Hver komplette runde har høyst 2 kandidater med scoren ved grense K = 5.

Luna og Haiku skal sjekkes med samme regel på sine
holdout-logger og må bestå på samme fire krav.

Utfall A, alle tre består: E5c med sumregel brukes for alle tre modeller i hovedkjøringen. Sumregelen legges inn i svarparser.py
med test før hovedkjøringen. 

Utfall B, NorMistral stryker: E5c brukes for luna og Haiku.
Hva som skjer med NorMistral og sumregelen, avgjøres utenfor denne testen.