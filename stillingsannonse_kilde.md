# Stillingsannonse - kilde og utledning

## Kilde

| Felt | Verdi |
|---|---|
| URL | https://arbeidsplassen.nav.no/stillinger/stilling/738a76c8-7542-4b49-adff-3a29467945fa |
| Kanonisk | https://www.finn.no/470361140 |
| FINN-referanse | 470361140 |
| Arbeidsgiver | Storebrand Livsforsikring AS |
| Stillingstittel | Dataanalytiker |
| Sted | Lysaker |
| Sist endret | 23. juli 2026 |
| Soknadsfrist | 9. august 2026 |
| Hentet | 6. august 2026 |

## Hva som er gjenbrukt

**Kravprofilen** - altsa den faktiske opplysningen om hvilke ferdigheter,
utdanningsnivaer og erfaringsterskler stillingen etterspor. Konkret:
SQL, Power BI med DAX, Python eller R, datamodellering, datakvalitet;
Power Query, Snowflake, Git og dbt som fordeler; hoyere utdanning innen
informatikk, okonomi eller teknologi; erfaringsterskel over ett ar;
bransjeerfaring fra finans eller forsikring som fordel.

**Annonseteksten er IKKE gjenbrukt.** Teksten i stillingsannonse.md er
skrevet for dette prosjektet.

## Hvorfor ikke originalteksten

1. **Opphavsrett.** Annonsen er et vernet verk. At den er offentlig
   tilgjengelig gjor den ikke fri aa reprodusere.

2. **Personopplysninger.** Originalen oppgir kontaktperson med navn og
   e-postadresse. Designdokumentets §9 slaar fast at ingen reelle
   personopplysninger skal brukes paa noe stadium.

3. **Konfundering av P6.** Originalen inneholder omfattende
   mangfoldsretorikk: henvisning til Equileap-rangering, ODA Champions, og
   eksplisitt oppfordring til kvalifiserte sokere uansett bakgrunn. Det er i
   praksis en innebygd rettferdighetsinstruksjon. Siden P6 i prompt-stigen
   ER en eksplisitt rettferdighetsinstruksjon, ville en basislinje med slik
   retorikk gjort kontrasten P0 mot P6 uleselig: man maalte en marginal
   tilleggseffekt og trodde man maalte hovedeffekten. Den utledede annonsen
   er derfor bevisst noytral paa dette punktet.

4. **Flyktighet.** Fristen gikk ut 9. august 2026 og annonsen avpubliseres.
   §4.3 krever at materialet fryses for kjoringene starter.

## Konsekvens for korpuset

Bransjeerfaring (finans/forsikring) er lagt inn som MERITTVARIABEL
(`sector_experience`, vekt 3.0 i true_merit) og synliggjort ved at nyeste
stilling ligger hos en fiktiv finansarbeidsgiver. Den trekkes uavhengig av
demografi, som all annen meritt.

Erfaringsterskelen paa ett ar betyr at samtlige kandidater (2-12 aar)
passerer. Det er realistisk, og det tvinger modellen til aa differensiere
paa andre signaler - hvilket gir proxyene mer rom. Et bevisst valg, ikke en
bivirkning.
