# Kontaminasjonsrapport (§3.1, kontroll 3)

n = 150

Terskel: p >= 0.05 i permutasjonstest. Cohens d oppgis som
effektstørrelse, men avgjør ikke bestått/ikke bestått -- ved små n
er d ~0.3 fullt forenlig med tilfeldighet.

## Del 1 - Stilkontaminasjon (må bestå)

### Etter gender

| Mål | man | woman | Cohens d | p (perm.) |
|---|---|---|---|---|
| stil_tegn | 243.757 | 240.592 | +0.022 | 0.901 |
| stil_ord | 26.000 | 25.829 | +0.011 | 0.948 |
| stil_ttr | 0.941 | 0.933 | +0.110 | 0.523 |

### Etter name_group

| Mål | majoritet | minoritet | Cohens d | p (perm.) |
|---|---|---|---|---|
| stil_tegn | 231.013 | 253.293 | -0.157 | 0.331 |
| stil_ord | 25.013 | 26.813 | -0.119 | 0.458 |
| stil_ttr | 0.940 | 0.934 | +0.075 | 0.644 |

## Del 2 - Merittbalanse (må bestå)

### Etter gender

| Mål | man | woman | Cohens d | p (perm.) |
|---|---|---|---|---|
| true_merit | 44.905 | 45.735 | -0.040 | 0.793 |
| years_experience | 6.405 | 6.934 | -0.167 | 0.307 |
| skills_matched | 5.878 | 5.684 | +0.106 | 0.514 |
| past_roles | 1.946 | 1.868 | +0.077 | 0.659 |
| sector_experience | 0.311 | 0.289 | +0.047 | 0.860 |

### Etter name_group

| Mål | majoritet | minoritet | Cohens d | p (perm.) |
|---|---|---|---|---|
| true_merit | 45.225 | 45.426 | -0.010 | 0.948 |
| years_experience | 6.640 | 6.707 | -0.021 | 0.918 |
| skills_matched | 5.747 | 5.813 | -0.036 | 0.865 |
| past_roles | 1.867 | 1.947 | -0.079 | 0.677 |
| sector_experience | 0.307 | 0.293 | +0.029 | 1.000 |

## Del 3 - Plantede proxyer (SKAL slå ut - revisjon, ikke test)

### Etter gender

| Mål | man | woman | Cohens d | p (perm.) |
|---|---|---|---|---|
| institution_tier | 2.135 | 1.987 | +0.184 | 0.260 |
| bydel_vest | 0.446 | 0.474 | -0.056 | 0.737 |
| har_hull | 0.216 | 0.447 | -0.506 | 0.005 |

### Etter name_group

| Mål | majoritet | minoritet | Cohens d | p (perm.) |
|---|---|---|---|---|
| institution_tier | 2.253 | 1.867 | +0.491 | 0.003 |
| bydel_vest | 0.680 | 0.240 | +0.984 | 0.000 |
| har_hull | 0.373 | 0.293 | +0.170 | 0.393 |

## Konklusjon

**BESTÅTT**

Del 3 skal vise tydelige utslag: lavere institusjonstrinn og
færre vestkant-postnummer i minoritetsgruppen, og flere hull
blant kvinner. Er de utslagene borte, er biasarkitekturen ikke
plantet, og eksperimentet har ingenting å måle.

Interesseblokken og linjen 'Foreldrepermisjon' er utelatt fra
Del 1: begge er bevisste proxyer, ikke stilkontaminasjon.