# M-OMNIA / PHI-INFINITY — stato della ricerca al 27 settembre 2026

**Tipo:** raccordo cronologico e protocollo operativo.
**Ambito:** ricerca corrente; non modifica il contratto congelato né il codice `src/`.

## A. Soluzione concettuale corrente

La formula madre minimale è \(M=(F\leftrightarrow F)^\infty\). Un nome umano
indica un accesso alla realtà, ma non genera la meccanica. La ricostruzione
parte da differenze, accessibilità reciproca, scambi, propagazioni, residui,
persistenza e riconfigurazione; solo dopo assegna nomi agli elementi
distinguibili.

La prima cascata concettuale conserva questi risultati:

1. **R1:** delimitazione \(\ne\) isolamento;
2. **R2:** parte \(\ne\) parte isolata;
3. **R3:** proprietà della configurazione \(\ne\) proprietà necessaria
   della parte considerata isolatamente.

Un dominio delimitato può scambiare con ciò che la rappresentazione pone
oltre il suo confine. Una perdita apparente al suo interno non autorizza a
cancellare la conseguenza o a chiamare zero quanto non è accessibile. La
frontiera va riaperta includendo gli scambi con l'ambiente, quando accessibili;
ciò che resta non discriminato rimane `UNRESOLVED`.

La meccanica madre congelata resta quella del contratto
[`UNIVERSAL_MOTHER_MECHANICS_CURRENT.md`](UNIVERSAL_MOTHER_MECHANICS_CURRENT.md),
SHA-256 `0cea8129245b212c04fa776bdc1b718fabf50998a9635e1e06716504fc410f7b`.
La formula minimale e la cascata esplicitano il lavoro concettuale successivo;
non sostituiscono retroattivamente il testo o i risultati del contratto.

## B. Percorso di lavoro

Per ogni nuovo caso:

1. Trattare la domanda come **AccessPointer** e applicare **DeName**.
2. Ricostruire la configurazione accessibile prima, durante e dopo lo scambio;
   includere le interfacce e le conseguenze attraverso le scale.
3. Produrre una soluzione concettuale interna a M, esplicitando le aperture
   incognite associate a ogni chiusura, quindi congelarla.
4. Documentare il percorso che ha prodotto la soluzione, compreso il test di
   sottrazione del tassello ritenuto necessario.
5. Solo alla fine definire quantità, operatori e predizioni numeriche.
6. Congelare condizioni di accettazione e confronto **prima** di osservare
   i dati di verifica. Registrare il primo fallimento; usare `REOPEN` per
   indagare la rappresentazione, non per cambiare retroattivamente il test.

Le categorie e i solutori preesistenti possono essere usati per confrontare
risultati dopo il congelamento; non sono sorgenti della derivazione in M. Un
fallimento documentato resta un fallimento del candidato testato. Nessuna
nuova soglia, eccezione o costante può essere inserita dopo aver visto il
risultato per trasformarlo in un successo.

## C. Formalizzazione corrente e stato di implementazione

| Relazione di lavoro | Significato operativo corrente | Stato nel repository |
| --- | --- | --- |
| \(\sum dS=0\) | Chiusura nel dominio conservativo completamente contabilizzato | Ipotesi di formalizzazione; le variabili e il confine vanno dichiarati nel singolo test. |
| \(\sum dS=\Phi_{\mathrm{dissipation}}\) | Estensione proposta per domini dissipativi o con transizione di fase | Da derivare operativamente e distinguere dagli scambi con l'ambiente. |
| \(d\tau_i\) | Progressione propria alla scala/configurazione, non un `dt` esterno generativo | Sviluppata nei manoscritti successivi; nessuna legge quantitativa universale è stata verificata nel runtime congelato. |
| \(P_{\mathrm{topo}}, S_{\mathrm{crit}}\) | Proiezione e soglia proposte per stati estremi | Nominati nel protocollo corrente; definizione eseguibile, derivazione e prova restano aperte. Non sono in `src/`. |
| \(M_{\mathrm{gate}}\) | Rifiuto/stop deterministico ex ante per una transizione specificata | Il runtime di agosto contiene un gate di accettazione generale; il confronto del 25 settembre è un artefatto separato. |

Il simbolo \(dS\) deve identificare una grandezza e un'orientazione precise nel
test: variazione di un vettore di stato, scambio con segno e lunghezza positiva
del percorso non sono automaticamente intercambiabili. Questo requisito
impedisce che una formula diventi un verdetto prima di definire cosa misura.

Il manoscritto sul tempo del 20 settembre usa anche \(dt=\kappa d\tau\), con
\(\kappa\approx3{,}19275\) nel benchmark descritto. In questa fase `dt` è
una traduzione verso letture temporali osservabili, non il parametro che
genera la ricostruzione. Il valore e la sua eventuale universalità sono
affermazioni del manoscritto: il presente aggiornamento non le promuove a
costanti del codice congelato.

## Progressione e precedenza delle versioni

| Fase | Documento/risultato | Rapporto con la fase corrente |
| --- | --- | --- |
| 30–31 agosto | Contratto congelato, due amendment e 46 casi oggi raccolti | Baseline storica protetta; non va riscritta. |
| Settembre, manoscritti M-OMNIA | Formalismo, Reality Gates, ricostruzione del fotone e trattato consegnati dall'autore | Sviluppi della ricerca, con affermazioni da tenere distinte dalle verifiche riprodotte nel repository. I PDF non sono pubblicati in questo aggiornamento. |
| 20 settembre | Manoscritto sul tempo geometrico | Sviluppo successivo del ramo temporale; non si legge il documento di agosto come veto a priori. Il PDF non è incluso qui. |
| 25 settembre | Manoscritto sull'invarianza runtime e [sintesi del confronto](validation/ADVERSARIAL_STRESS_TEST_2026-09-25.md) | Risultato nel simulatore definito; non dimostrazione fisica generale. I file originali non sono pubblicati qui. |
| 27 settembre | Protocollo di inizializzazione fornito dall'autore | Stato concettuale corrente; l'implementazione nuova richiede derivazione e prova separate. |

I file più recenti sviluppano e possono correggere i precedenti. I documenti
di agosto etichettati `CURRENT` appartengono allo stato allora congelato del
repository. Una differenza tra loro e un manoscritto di settembre non è, da
sola, una contraddizione all'interno dell'ultima formulazione.

## Confini della prova

- I 46 test locali controllano proprietà del codice di agosto; non verificano
  automaticamente le proposizioni fisiche dei manoscritti successivi.
- I Reality Gates riportati nei manoscritti sono risultati dichiarati nei
  rispettivi lavori. Solo i gate, i dati e gli output presenti in questo
  repository sono riproducibili da esso.
- Il confronto del 25 settembre è qui riassunto dai file forniti dall'autore,
  ma né la traccia numerica originale né `simulation.py` sono in questo
  repository: il risultato non è riproducibile da esso.
- Le prove negative restano nel registro; la regola **No-Retrofit** vieta di
  cambiare il candidato congelato per ottenere il risultato desiderato.

**Prossima apertura concreta:** definire, dalla meccanica concettuale congelata,
la quantità conservata, il confine e il termine dissipativo in un caso con
scambio ambientale osservabile; poi preregistrare la predizione e il suo
criterio di smentita. In parallelo, rendere derivabili e verificabili
\(P_{\mathrm{topo}}\) e \(S_{\mathrm{crit}}\) prima di introdurli nel motore.
