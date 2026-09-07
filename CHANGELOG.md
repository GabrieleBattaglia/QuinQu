# Changelog, Quinqu

Tutti i cambiamenti e le novità introdotte nelle versioni di Quinqu.
Il changelog nasce con la versione 4.5.0. Per le versioni precedenti il resoconto sta nella cronologia dei commit e nelle release pubblicate su GitHub.

## [4.5.0] - 2026-09-07

Fase 1 del refactoring generale, più la funzionalità chiesta dalla issue 1.

### Aggiunto

- **Tappe** (issue 1). Alla creazione di un obiettivo si sceglie in quante tappe raggiungerlo, oppure quanto larga debba essere ognuna, e la scelta si conferma con `enter_escape`. Il numero di tappe viene salvato nel json dell'obiettivo.
- Nuova voce di menu **tappe**, che disegna una barra a celle sulla scala che va dal valore di partenza all'obiettivo. `I` è l'inizio e `F` il traguardo, ogni tappa porta il proprio numero, `T` è il tempo trascorso, `O` il valore attuale, `M` `X` e `D` il minimo, il massimo e la media dei valori registrati. Le celle libere si riempiono con cinque gradazioni ASCII, dal punto al cancelletto, in proporzione alla parte di percorso già coperta.
- La barra **non ha lunghezza fissa**: cresce di otto celle per tappa, con un minimo di settantacinque, e va a capo ogni settantacinque caratteri. Così le tappe non hanno più un tetto di dieci e non si toccano mai fra loro.
- Quando due o più marcatori cadono nella stessa cella, le loro etichette si scrivono **unite**, prima il numero della tappa e poi le lettere: `IX` dove il massimo coincide con la partenza, `8OM` dove la tappa 8 sta sul valore di oggi che è anche il minimo, `10F` dove l'ultima tappa è il traguardo. Nessun marcatore resta nascosto e non serve nessun carattere speciale per segnalare l'incontro.
- **Sopra la barra, la situazione raccontata a parole**, per chi non legge sul display braille: dove sei, quanto percorso hai coperto, quanto tempo è passato, quale sarebbe il valore giusto adesso, di quanto sei avanti o indietro sul tempo, fra quali due tappe ti trovi, di quanto hai superato l'ultima, quanto manca alla prossima e a che punto sei dentro la tappa in corso, più minimo, massimo e media.
- La barra è pensata per il display braille: il cursore della console viene **riportato all'inizio della barra** e il programma **aspetta in silenzio la pressione di un tasto** prima di proseguire con la legenda. Dove l'interpretazione ANSI della console non si riesce ad accendere, il cursore resta comunque su una riga della barra e non su quella vuota sotto.
- Prima della barra una legenda compatta dice solo in quale cella sta ogni lettera: i valori li ha già detti il racconto. Sta in righe intere e non spezzate ogni quaranta caratteri, perché sono spiegazioni da leggere e non simboli da toccare.
- L'**elenco delle tappe con i loro valori** compare al momento di sceglierle, dove serve a decidere, e la conferma con `enter_escape` arriva dopo averlo letto.
- Nuova voce di menu **dividi**, per rivedere in quante tappe è diviso un obiettivo già avviato.
- **Il raggiungimento di una tappa si sente e si dice.** Registrando un valore che supera una tappa, l'applicazione lo annuncia e suona `jingle_livello_superato`; se ne supera più d'una dice da quale a quale; se si torna indietro sotto una tappa già raggiunta lo dice con `spirale_discendente`.
- Il **valore giusto**, quello sincronizzato con lo scorrere del tempo, cade per definizione sempre nella cella di `T`: non ha una lettera propria e compare come numero nel racconto sopra la barra.
- Controllo automatico degli aggiornamenti all'avvio, affidato a `gestisci_aggiornamento` di GBUtils, come in tutti gli altri progetti del parco.
- Salvataggio automatico e silenzioso dopo ogni comando che modifica i dati. Prima i valori inseriti restavano in memoria fino al comando `salva` o all'uscita.
- Copia di sicurezza `quinqu.json.bak`, riscritta a ogni salvataggio riuscito.
- File di contorno finora assenti: `CHANGELOG.md`, `requirements.txt`, `quinqu.spec` per PyInstaller e `ruff.toml`.

### Corretto

- **Un solo record malformato non porta più via l'intero archivio.** Il caricamento valida gli obiettivi uno per uno, dice quali scarta e distingue l'archivio assente da quello illeggibile: nel secondo caso l'applicazione si ferma senza salvare, invece di sovrascrivere il file con un archivio nuovo.
- **Il progetto concluso non viene più cancellato quando il report non si scrive.** La funzione che produce il report restituiva sempre esito positivo, anche dopo un errore: bastava un nome di progetto con i due punti o la barra, che Windows rifiuta nei nomi di file, per perdere insieme il report e il progetto. Ora il nome viene ripulito, un report omonimo non viene sovrascritto e il progetto resta nell'archivio finché il file non esiste davvero.
- **La proiezione non fa più cadere l'applicazione.** Con i valori in stallo la pendenza della retta è quasi zero e il traguardo finiva oltre l'anno 9999, con un `OverflowError` non gestito subito dopo l'inserimento di un valore, che a quel punto andava perso. Ora c'è un orizzonte di cento anni e la costruzione della data è protetta.
- **Il salvataggio è atomico.** Si scrive su un file temporaneo nella stessa cartella e si sostituisce con `os.replace`: un'interruzione a metà non può più lasciare un `quinqu.json` troncato.
- **I dati stanno accanto al programma, non nella directory di lavoro.** Archivio, archivio vecchio e report usano ora percorsi assoluti ricavati da `sys.executable` quando si gira da eseguibile e da `__file__` quando si gira da sorgente. Lanciando l'eseguibile da un collegamento, Quinqu non cerca più i propri dati altrove.
- **Control C non butta più via la sessione.** L'interruzione da tastiera salva e saluta, e un errore imprevisto si presenta in italiano invece che come traccia di stack.
- **La data non fa più cadere l'applicazione negli ultimi giorni del mese.** Premendo invio sul giorno, `dgt` restituisce il valore predefinito senza applicare i limiti: il 31 di marzo, scegliendo febbraio, produceva una data inesistente. Il predefinito viene ora limitato al massimo del mese, che si chiede a `calendar.monthrange`.
- **La deviazione dal valore ideale si misura sull'ampiezza dell'obiettivo.** Prima si divideva per il valore ideale, e mezzo chilo di ritardo su cinque da perdere appariva come lo 0,5 per cento invece che come il dieci.
- **La proiezione tace quando i dati sono troppo ravvicinati.** Con due valori a un minuto di distanza annunciava il traguardo per due minuti dopo. Ora serve almeno un giorno di dati.
- Due valori registrati nello stesso secondo non si sovrappongono più: il secondo scala in avanti finché non trova un istante libero.
- I limiti dei valori registrabili sono una sola coppia di costanti, applicata anche al comando `nuovo`, che prima non ne applicava nessuno. L'intervallo si allarga da 0 e 1000 a meno un milione e più un milione, così `dgt` non corregge più in silenzio quello che si era inteso davvero.
- Il confronto fra tempo e valore dice chi dei due è avanti, invece di mostrare uno scarto con il segno.
- La data di inizio nel futuro viene segnalata e chiede conferma.

### Modificato

- **Accessibilità.** Tolte le venticinque righe vuote di separazione e i rientri con tabulazione delle statistiche. Le righe informative sono spezzate in blocchi di circa quaranta caratteri per la lettura sul display braille. Il tabellino di marcia nomina ogni valore accanto al suo numero, invece di affidare l'informazione al solo ordine dei numeri.
- **DRY.** Le due proiezioni, le righe del registro e la conclusione di un progetto stavano scritte due volte ciascuna; il confronto ricalcolava a mano le percentuali che due funzioni già restituivano. Ora c'è una funzione sola per ognuna di queste cose.
- Il comando `nuovo` legge con `dgt` invece che con `input`, quindi si comporta come tutti gli altri prompt e l'invio a vuoto riporta al menu.
- La regressione delle proiezioni lavora su tempi relativi al primo dato invece che sui timestamp assoluti: stesso risultato, senza il malcondizionamento che poteva far comparire un avviso di numpy in mezzo ai risultati.
- Versione e data di rilascio sono due costanti separate, `APP_VERSION` e `RELEASE_DATE`, come nel resto del parco software.
- I sei `except Exception` nudi sono stati sostituiti dalle eccezioni che ci si aspetta davvero, con una sola rete di sicurezza in fondo a `main`.
- `calendar.monthrange` al posto del calcolo a mano dei giorni del mese, bisestili compresi.
- Il validatore `ruff` passa senza rilievi, con la configurazione dedicata di `ruff.toml`.
