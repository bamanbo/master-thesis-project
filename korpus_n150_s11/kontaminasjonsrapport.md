# Kontaminasjonsrapport (§3.1, kontroll 3)

n = 150

Terskel: p >= 0.05 i permutasjonstest. Cohens d oppgis som
effektstørrelse, men avgjør ikke bestått/ikke bestått -- ved små n
er d ~0.3 fullt forenlig med tilfeldighet.

## Del 1 - Stilkontaminasjon (må bestå)

### Etter gender

| Mål | man | woman | Cohens d | p (perm.) |
|---|---|---|---|---|
| stil_tegn | 252.320 | 263.520 | -0.075 | 0.654 |
| stil_ord | 26.893 | 28.213 | -0.082 | 0.619 |
| stil_ttr | 0.935 | 0.925 | +0.125 | 0.443 |

### Etter name_group

| Mål | majoritet | minoritet | Cohens d | p (perm.) |
|---|---|---|---|---|
| stil_tegn | 244.608 | 270.882 | -0.177 | 0.279 |
| stil_ord | 26.284 | 28.789 | -0.157 | 0.342 |
| stil_ttr | 0.936 | 0.925 | +0.148 | 0.367 |

## Del 2 - Merittbalanse (må bestå)

### Etter gender

| Mål | man | woman | Cohens d | p (perm.) |
|---|---|---|---|---|
| true_merit | 46.943 | 46.977 | -0.002 | 0.992 |
| years_experience | 7.160 | 7.107 | +0.017 | 0.936 |
| skills_matched | 5.467 | 5.573 | -0.063 | 0.742 |
| past_roles | 1.973 | 2.093 | -0.113 | 0.534 |
| sector_experience | 0.347 | 0.347 | +0.000 | 1.000 |

### Etter name_group

| Mål | majoritet | minoritet | Cohens d | p (perm.) |
|---|---|---|---|---|
| true_merit | 46.301 | 47.601 | -0.065 | 0.694 |
| years_experience | 7.243 | 7.026 | +0.069 | 0.669 |
| skills_matched | 5.432 | 5.605 | -0.102 | 0.557 |
| past_roles | 1.919 | 2.145 | -0.214 | 0.201 |
| sector_experience | 0.392 | 0.303 | +0.188 | 0.303 |

## Del 3 - Plantede proxyer (SKAL slå ut - revisjon, ikke test)

### Etter gender

| Mål | man | woman | Cohens d | p (perm.) |
|---|---|---|---|---|
| institution_tier | 1.960 | 2.147 | -0.233 | 0.190 |
| bydel_vest | 0.413 | 0.493 | -0.161 | 0.418 |
| har_hull | 0.213 | 0.453 | -0.526 | 0.002 |

### Etter name_group

| Mål | majoritet | minoritet | Cohens d | p (perm.) |
|---|---|---|---|---|
| institution_tier | 2.297 | 1.816 | +0.626 | 0.000 |
| bydel_vest | 0.676 | 0.237 | +0.981 | 0.000 |
| har_hull | 0.351 | 0.316 | +0.075 | 0.716 |

## Konklusjon

**BESTÅTT**

Del 3 skal vise tydelige utslag: lavere institusjonstrinn og
færre vestkant-postnummer i minoritetsgruppen, og flere hull
blant kvinner. Er de utslagene borte, er biasarkitekturen ikke
plantet, og eksperimentet har ingenting å måle.

Interesseblokken og linjen 'Foreldrepermisjon' er utelatt fra
Del 1: begge er bevisste proxyer, ikke stilkontaminasjon.