# Kontaminasjonsrapport (§3.1, kontroll 3)

n = 40

Terskel: p >= 0.05 i permutasjonstest. Cohens d oppgis som
effektstørrelse, men avgjør ikke bestått/ikke bestått -- ved små n
er d ~0.3 fullt forenlig med tilfeldighet.

## Del 1 - Stilkontaminasjon (må bestå)

### Etter gender

| Mål | man | woman | Cohens d | p (perm.) |
|---|---|---|---|---|
| stil_tegn | 267.650 | 250.250 | +0.125 | 0.707 |
| stil_ord | 28.950 | 26.450 | +0.166 | 0.618 |
| stil_ttr | 0.929 | 0.939 | -0.151 | 0.657 |

### Etter name_group

| Mål | majoritet | minoritet | Cohens d | p (perm.) |
|---|---|---|---|---|
| stil_tegn | 267.200 | 250.700 | +0.118 | 0.716 |
| stil_ord | 28.350 | 27.050 | +0.086 | 0.797 |
| stil_ttr | 0.931 | 0.937 | -0.082 | 0.807 |

## Del 2 - Merittbalanse (må bestå)

### Etter gender

| Mål | man | woman | Cohens d | p (perm.) |
|---|---|---|---|---|
| true_merit | 47.568 | 49.928 | -0.122 | 0.703 |
| years_experience | 7.300 | 7.650 | -0.121 | 0.748 |
| skills_matched | 5.100 | 5.750 | -0.450 | 0.198 |
| past_roles | 2.200 | 1.950 | +0.256 | 0.522 |
| sector_experience | 0.350 | 0.450 | -0.205 | 0.743 |

### Etter name_group

| Mål | majoritet | minoritet | Cohens d | p (perm.) |
|---|---|---|---|---|
| true_merit | 48.737 | 48.759 | -0.001 | 0.998 |
| years_experience | 7.500 | 7.450 | +0.017 | 1.000 |
| skills_matched | 5.350 | 5.500 | -0.101 | 0.797 |
| past_roles | 2.150 | 2.000 | +0.153 | 0.533 |
| sector_experience | 0.500 | 0.300 | +0.417 | 0.335 |

## Del 3 - Plantede proxyer (SKAL slå ut - revisjon, ikke test)

### Etter gender

| Mål | man | woman | Cohens d | p (perm.) |
|---|---|---|---|---|
| institution_tier | 2.200 | 1.900 | +0.379 | 0.328 |
| bydel_vest | 0.400 | 0.550 | -0.304 | 0.530 |
| har_hull | 0.200 | 0.450 | -0.554 | 0.182 |

### Etter name_group

| Mål | majoritet | minoritet | Cohens d | p (perm.) |
|---|---|---|---|---|
| institution_tier | 2.200 | 1.900 | +0.379 | 0.347 |
| bydel_vest | 0.700 | 0.250 | +1.009 | 0.010 |
| har_hull | 0.300 | 0.350 | -0.107 | 1.000 |

## Konklusjon

**BESTÅTT**

Del 3 skal vise tydelige utslag: lavere institusjonstrinn og
færre vestkant-postnummer i minoritetsgruppen, og flere hull
blant kvinner. Er de utslagene borte, er biasarkitekturen ikke
plantet, og eksperimentet har ingenting å måle.

Interesseblokken og linjen 'Foreldrepermisjon' er utelatt fra
Del 1: begge er bevisste proxyer, ikke stilkontaminasjon.