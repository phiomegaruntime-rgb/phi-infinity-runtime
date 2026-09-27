# Confronto sotto stress del 25 settembre 2026 — sintesi dei risultati

**Classe di evidenza:** simulazione comparativa a seed fissato, non osservazione
fisica e non test del motore `src/` del repository.

Il manoscritto fornito dall'autore riporta `SEED = 20260925`. I conteggi
seguenti sono stati verificati sui file CSV, log e immagine consegnati
separatamente per questa revisione. **I file grezzi e il programma originale
`simulation.py` non sono pubblicati in questo repository**; i conteggi non
sono pertanto riproducibili da questo checkout.

Un [audit eseguibile](../../validation/gates/stress_test_artifact_audit.py)
permette di verificare hash, coerenza CSV/log e conteggi quando si disponga
dei tre file originali. Esecuzione, dalla radice del repository:

```bash
python validation/gates/stress_test_artifact_audit.py /percorso/agli/output_originali
```

L'audit non rigenera i dati: il codice generatore non è stato consegnato con
gli output e non va ricostruito a posteriori come se fosse l'originale.

## Risultati letti dal CSV, senza ricalibrazione

| Misura | Risultato |
| --- | ---: |
| Cicli registrati | 100 (passi 1–100) |
| Prima corruzione del controllo aperto | Passo 16 |
| Drift del controllo al passo 16 | 177.08721760057597 |
| Transizioni accettate nel sistema PHI del simulatore | 20 |
| Transizioni `REJECT_NON_CONSERVATIVE` | 80 |
| Cicli con `phi_halted=1` | 0 |
| Stato PHI finale del simulatore | 106.2790943851747 |
| Residuo PHI finale del simulatore | 20.696045734309212 |

La serie dimostra **solo nel modello simulato** che, con quel seed e quelle
regole, il controllo aperto entra nello stato etichettato `corrupted` al
passo 16, mentre il secondo sistema rifiuta 80 transizioni e non attiva
lo stop `M_gate`. I rifiuti non equivalgono a una soluzione del compito:
registrano anche una limitazione di disponibilità (80 proposte non eseguite).
Non si inferiscono immunità assoluta, prestazioni fisiche o superiorità
universale da un singolo seed e da un controllo costruito ad hoc.
La figura affianca il drift cumulativo del controllo e il residuo `phi_R`:
sono metriche diverse, quindi la distanza visiva fra le curve non misura
direttamente un miglioramento sullo stesso errore.

## Prossimo gate

Congelare **prima** di nuove esecuzioni un confronto con più seed e un
controllo di sicurezza convenzionale, includendo transizioni accettate,
falsi rifiuti, errori non intercettati, costo e criterio di successo.
Conservare l'esito di questo seed e il codice che lo ha generato; nessuna
soglia o etichetta del 25 settembre va ritarata a posteriori.
