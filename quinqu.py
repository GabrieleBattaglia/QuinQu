# Quanto in Quanto (Quinqu). Data di concepimento 10/02/2024.
# Programma per seguire e salvare i progressi nel raggiungimento di un obiettivo
# il cui valore possa essere espresso in numeri.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5, modalita' auto)

import calendar
import contextlib
import datetime as dt
import io
import itertools
import json
import os
import pickle
import shutil
import statistics
import sys
import tempfile
import warnings
from fractions import Fraction as frac

import numpy as np
from GBUtils import Acusticator, dgt, enter_escape, gestisci_aggiornamento, key, menu, sonify

APP_NAME = "Quinqu"
APP_VERSION = "4.5.0"
RELEASE_DATE = "2026-09-07"
AUTORE = "Gabriele"
RECORDNAME = "quinqu.json"
OLD_RECORDNAME = "quinqu.db"
API_RELEASE = "https://api.github.com/repos/GabrieleBattaglia/QuinQu/releases/latest"
# Larghezza dei blocchi in cui si spezzano le righe informative, per la
# lettura sul display braille.
LARGHEZZA_BLOCCO = 40
# Limiti dei valori registrabili. Stanno qui una volta sola perche' prima
# erano scritti a mano in quattro punti e in un quinto mancavano del tutto.
VALORE_MIN = -1000000.0
VALORE_MAX = 1000000.0
MAX_PROGETTI = 10
MINIMO_VALORI_STATISTICHE = 4
PUNTI_PROIEZIONE_RECENTE = 5
# Oltre cento anni la proiezione non e' piu' una previsione ma un modo di
# dire che, di questo passo, al traguardo non ci si arriva.
ORIZZONTE_PROIEZIONE_GIORNI = 36500
# Sotto un giorno di dati la retta di regressione non dice niente di
# utile: due valori a un minuto di distanza producono velocita' enormi.
SPAN_MINIMO_PROIEZIONE = 86400.0
# Scarto in punti percentuali entro cui tempo e valore si dicono allineati.
TOLLERANZA_CONFRONTO = 10.0
# Barra delle tappe. La prima cella e' l'inizio e l'ultima il traguardo, ma
# la lunghezza non e' fissa: cresce con il numero delle tappe, perche' due
# tappe non devono mai toccarsi, e va a capo ogni LARGHEZZA_RIGA caratteri.
# Le gradazioni del riempimento sono ASCII per restare leggibili sul braille.
LARGHEZZA_RIGA = 75
CELLE_PER_TAPPA = 8
GRADAZIONI = ".:+*#"
TAPPE_MIN = 2
# Il tetto non limita la scelta ma protegge lo schermo: con cento tappe la
# barra occupa gia' undici righe e la legenda cento.
TAPPE_MAX = 100
TAPPE_PREDEFINITE = 10
# I caratteri che Windows non ammette nei nomi di file.
VIETATI_NEI_NOMI = '<>:"/\\|?*'


def cartella_applicazione():
    """La cartella in cui stanno i dati, sia da sorgente sia da eseguibile.

    I nomi dei file erano relativi alla directory di lavoro, quindi Quinqu
    cercava l'archivio dove si trovava la console al momento del lancio.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


CARTELLA = cartella_applicazione()
PERCORSO_RECORD = os.path.join(CARTELLA, RECORDNAME)
PERCORSO_OLD = os.path.join(CARTELLA, OLD_RECORDNAME)
PERCORSO_BACKUP = PERCORSO_RECORD + ".bak"

main_menu = {
    "nuovo": "Nuova registrazione del valore",
    "apri": "Apri un nuovo obiettivo",
    "cancella": "Cancella un valore",
    "fine": "Modifica la data di fine progetto",
    "obiettivo": "Modifica l'obiettivo",
    "registro": "Mostra il registro",
    "suono_p": "Ascolta l'andamento dei valori (portamento)",
    "suono_np": "Ascolta l'andamento dei valori (No portamento)",
    "suono_d": "Ascolta l'andamento dei valori (scegli durata)",
    "progresso_ob": "Vedi il progresso rispetto all'obiettivo",
    "progresso_t": "Vedi il progresso rispetto al tempo",
    "confronto": "Confronta tempo e obiettivo",
    "tappe": "Mostra la barra delle tappe",
    "dividi": "Modifica in quante tappe è diviso l'obiettivo",
    "statistiche": "Informazioni statistiche",
    "salva": "Salva il registro",
    "cambia": "Cambia obiettivo gestito",
    "elimina": "Elimina l'obiettivo corrente",
    "menu": "Mostra il menù",
    "reset": "Elimina definitivamente tutti i dati (RESET GLOBALE)",
    "esci": "Esci dall'App",
}


def RiproduciEffetto(nome_preset, base_vol=0.4, sync=True):
    """Suona un effetto della collezione condivisa, chiamandolo per nome.

    Resta un involucro attorno ad Acusticator.play soltanto per tenere in un
    posto solo le due scelte di Quinqu: il volume base su cui si applicano
    gli scarti scritti nella collezione, e la riproduzione sincrona.
    Restituisce True se il suono e' partito.
    """
    return Acusticator.play(nome_preset, sync=sync, volume=base_vol)


def blocchi(testo, larghezza=LARGHEZZA_BLOCCO):
    """Spezza un testo in righe di circa larghezza caratteri, senza tagliare le parole."""
    righe = []
    corrente = ""
    for parola in testo.split():
        if not corrente:
            corrente = parola
        elif len(corrente) + 1 + len(parola) <= larghezza:
            corrente += " " + parola
        else:
            righe.append(corrente)
            corrente = parola
    if corrente:
        righe.append(corrente)
    return righe


def dillo(testo):
    """Stampa un testo informativo in blocchi di circa quaranta caratteri."""
    for riga in blocchi(testo):
        print(riga)


def impacchetta(voci, larghezza=LARGHEZZA_BLOCCO):
    """Raggruppa voci brevi in righe di circa larghezza caratteri.

    A differenza di blocchi, che puo' andare a capo dentro una voce, qui il
    taglio cade sempre fra una voce e l'altra: una riga che finisce con
    "T" e riprende con "cella 41" non si legge.
    """
    righe = []
    corrente = ""
    for voce in voci:
        if not corrente:
            corrente = voce
        elif len(corrente) + 2 + len(voce) <= larghezza:
            corrente += ", " + voce
        else:
            righe.append(corrente)
            corrente = voce
    if corrente:
        righe.append(corrente)
    return righe


def ValoreIniziale(stato):
    """Il valore del record piu' vecchio del registro."""
    return stato["valori"][min(stato["valori"])][0]


def ValoreAttuale(stato):
    """Il valore del record piu' recente del registro."""
    return stato["valori"][max(stato["valori"])][0]


def Salva(progetti, annuncia=True):
    """Scrive l'archivio su disco. Restituisce True se il salvataggio e' riuscito.

    La scrittura avviene su un file temporaneo nella stessa cartella e la
    sostituzione con os.replace e' atomica: un'interruzione a meta' non puo'
    piu' lasciare un quinqu.json troncato. La versione precedente resta
    accanto come quinqu.json.bak.
    Con annuncia a False non suona e non stampa: e' il salvataggio
    automatico che segue ogni modifica.
    """
    temporaneo = None
    try:
        progetti_json = {}
        for pid, p in progetti.items():
            valori_ser = {}
            for k, v in p["valori"].items():
                valori_ser[k.isoformat()] = v if isinstance(v, list) else [v, ""]
            progetti_json[pid] = {
                "prjnome": p["prjnome"],
                "prjdesc": p["prjdesc"],
                "datainizio": p["datainizio"].isoformat(),
                "datafine": p["datafine"].isoformat(),
                "valori": valori_ser,
                "obiettivo": p["obiettivo"],
                "tappe": p.get("tappe"),
            }
        descrittore, temporaneo = tempfile.mkstemp(prefix="quinqu-", suffix=".tmp", dir=CARTELLA)
        with os.fdopen(descrittore, "w", encoding="utf-8") as f:
            json.dump(progetti_json, f, indent=4, ensure_ascii=False)
        if os.path.exists(PERCORSO_RECORD):
            shutil.copy2(PERCORSO_RECORD, PERCORSO_BACKUP)
        os.replace(temporaneo, PERCORSO_RECORD)
        temporaneo = None
    except (OSError, TypeError, ValueError, AttributeError, KeyError) as e:
        print(f"Errore durante il salvataggio: {e}")
        if temporaneo and os.path.exists(temporaneo):
            with contextlib.suppress(OSError):
                os.remove(temporaneo)
        return False
    if annuncia:
        RiproduciEffetto("written_ok")
        print(f"{RECORDNAME} salvato.")
    return True


def _valida_progetto(grezzo):
    """Controlla un progetto letto dal file e lo restituisce convertito.

    Solleva ValueError con il motivo quando il record non e' utilizzabile.
    Serve a non buttare via l'intero archivio per colpa di un solo record.
    """
    if not isinstance(grezzo, dict):
        raise ValueError("il record non è un dizionario")
    for chiave in ("prjnome", "prjdesc", "datainizio", "datafine", "valori", "obiettivo"):
        if chiave not in grezzo:
            raise ValueError(f"manca il campo {chiave}")
    try:
        datainizio = dt.datetime.fromisoformat(str(grezzo["datainizio"]))
        datafine = dt.datetime.fromisoformat(str(grezzo["datafine"]))
    except (TypeError, ValueError) as e:
        raise ValueError(f"data del progetto non leggibile, {e}") from e
    if datafine <= datainizio:
        raise ValueError("la data di fine non è successiva a quella di inizio")
    if not isinstance(grezzo["valori"], dict) or not grezzo["valori"]:
        raise ValueError("il registro dei valori è vuoto o malformato")
    valori = {}
    for k, v in grezzo["valori"].items():
        try:
            quando = dt.datetime.fromisoformat(str(k))
        except (TypeError, ValueError) as e:
            raise ValueError(f"data di un valore non leggibile, {k}") from e
        try:
            if isinstance(v, list):
                if not v:
                    raise ValueError("valore vuoto")
                numero = float(v[0])
                commento = str(v[1]) if len(v) > 1 and v[1] else ""
            else:
                numero = float(v)
                commento = ""
        except (TypeError, ValueError) as e:
            raise ValueError(f"valore non numerico in data {k}") from e
        valori[quando] = [numero, commento]
    try:
        obiettivo = float(grezzo["obiettivo"])
    except (TypeError, ValueError) as e:
        raise ValueError("obiettivo non numerico") from e
    tappe = grezzo.get("tappe")
    if tappe is not None:
        try:
            tappe = int(tappe)
        except (TypeError, ValueError):
            tappe = None
        else:
            if not TAPPE_MIN <= tappe <= TAPPE_MAX:
                tappe = None
    return {
        "prjnome": str(grezzo["prjnome"]),
        "prjdesc": str(grezzo["prjdesc"]),
        "datainizio": datainizio,
        "datafine": datafine,
        "valori": valori,
        "obiettivo": obiettivo,
        "tappe": tappe,
    }


def Carica():
    """Legge l'archivio. Restituisce la terna progetti, errore, scartati.

    errore vale None quando la lettura e' andata bene, altrimenti contiene il
    motivo: in quel caso il chiamante non deve salvare niente, perche' il file
    sul disco potrebbe essere ancora recuperabile a mano.
    scartati elenca i record singoli che non hanno superato la validazione.
    """
    if os.path.exists(PERCORSO_RECORD):
        try:
            with open(PERCORSO_RECORD, encoding="utf-8") as f:
                dati = json.load(f)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            return {}, f"{RECORDNAME} non è leggibile: {e}", []
        if not isinstance(dati, dict):
            return {}, f"{RECORDNAME} non contiene un archivio di obiettivi", []
        if "prjnome" in dati:
            dati = {"0": dati}
        progetti = {}
        scartati = []
        for pid, grezzo in dati.items():
            try:
                progetti[str(pid)] = _valida_progetto(grezzo)
            except ValueError as e:
                scartati.append(f"obiettivo {pid}: {e}")
        if not progetti and scartati:
            return {}, f"nessun obiettivo di {RECORDNAME} è utilizzabile", scartati
        return progetti, None, scartati
    if os.path.exists(PERCORSO_OLD):
        return _migra_dal_pickle()
    return {}, None, []


def _migra_dal_pickle():
    """Converte il vecchio archivio pickle nel formato json. Stessa terna di Carica."""
    try:
        with open(PERCORSO_OLD, "rb") as f:
            dati = pickle.load(f)
            if isinstance(dati, dict):
                stato = dati
            else:
                stato = {
                    "prjnome": dati,
                    "prjdesc": pickle.load(f),
                    "datainizio": pickle.load(f),
                    "datafine": pickle.load(f),
                    "valori": pickle.load(f),
                    "obiettivo": pickle.load(f),
                }
    except (OSError, pickle.UnpicklingError, EOFError, AttributeError, ImportError, IndexError) as e:
        return {}, f"{OLD_RECORDNAME} non è leggibile: {e}", []
    grezzo = dict(stato)
    for chiave in ("datainizio", "datafine"):
        if isinstance(grezzo.get(chiave), dt.datetime):
            grezzo[chiave] = grezzo[chiave].isoformat()
    if isinstance(grezzo.get("valori"), dict):
        grezzo["valori"] = {(k.isoformat() if isinstance(k, dt.datetime) else str(k)): v for k, v in grezzo["valori"].items()}
    try:
        progetto = _valida_progetto(grezzo)
    except ValueError as e:
        return {}, f"{OLD_RECORDNAME} contiene dati non utilizzabili: {e}", []
    dillo(f"Trovato il vecchio {OLD_RECORDNAME}.")
    print("Conversione in formato JSON in corso.")
    progetti = {"0": progetto}
    if not Salva(progetti, annuncia=False):
        return {}, "la conversione non è riuscita a scrivere il nuovo archivio", []
    try:
        os.rename(PERCORSO_OLD, PERCORSO_OLD + ".bak")
        dillo(f"Il vecchio file è stato rinominato in {OLD_RECORDNAME}.bak per sicurezza.")
    except OSError as e:
        dillo(f"Il vecchio file non è stato rinominato: {e}")
    return progetti, None, []


def DigitaData():
    """Chiede una data completa, campo per campo, e la restituisce."""
    oggi = dt.datetime.now().replace(microsecond=0)
    anno = dgt(prompt=f"Anno? invio={oggi.year}> ", kind="i", imin=1970, imax=2500, default=oggi.year)
    mese = dgt(prompt=f"Mese? invio={oggi.month}> ", kind="i", imin=1, imax=12, default=oggi.month)
    maxgiorno = calendar.monthrange(anno, mese)[1]
    # Il valore predefinito va limitato qui: dgt, quando si preme invio, lo
    # restituisce senza applicare imin e imax, e il 31 di un mese corto
    # farebbe fallire la costruzione della data.
    giorno_default = min(oggi.day, maxgiorno)
    giorno = dgt(prompt=f"Giorno? invio={giorno_default}, max={maxgiorno}> ", kind="i", imin=1, imax=maxgiorno, default=giorno_default)
    ora = dgt(prompt=f"A che ora? invio={oggi.hour}> ", kind="i", imin=0, imax=23, default=oggi.hour)
    minuto = dgt(prompt=f"Minuti? invio={oggi.minute}> ", kind="i", imin=0, imax=59, default=oggi.minute)
    print("Grazie")
    return dt.datetime(year=anno, month=mese, day=giorno, hour=ora, minute=minuto)


def ConfiguraTappe(stato):
    """Chiede in quante tappe dividere il percorso, oppure quanto larga sia ognuna.

    Restituisce il numero di tappe confermato, oppure None se non se n'e'
    scelta nessuna. Ogni tappa porta sulla barra il proprio numero scritto
    per esteso, quindi non c'e' nessun tetto legato alle cifre: la barra si
    allunga quanto serve perche' ci stiano tutte senza toccarsi.
    """
    vi = ValoreIniziale(stato)
    ob = stato["obiettivo"]
    ampiezza = abs(ob - vi)
    if ampiezza == 0:
        print("Valore iniziale e obiettivo coincidono:")
        print("non c'è nessun percorso da dividere.")
        return None
    print("Suddivisione del percorso in tappe.")
    dillo(f"Si va da {vi:+.2f} a {ob:+.2f}, per un'ampiezza di {ampiezza:.2f}.")
    modi = {"numero": "Dico io quante tappe voglio", "ampiezza": "Dico io quanto è larga una tappa"}
    while True:
        modo = menu(d=modi, p="Come preferisci? ", show=True, keyslist=True)
        if modo is None:
            return None
        if modo == "numero":
            tappe = dgt(
                prompt=f"Quante tappe? da {TAPPE_MIN} a {TAPPE_MAX}, invio={TAPPE_PREDEFINITE}> ",
                kind="i",
                imin=TAPPE_MIN,
                imax=TAPPE_MAX,
                default=TAPPE_PREDEFINITE,
            )
            tappe = max(TAPPE_MIN, min(TAPPE_MAX, int(tappe)))
        else:
            minima = ampiezza / TAPPE_MAX
            massima = ampiezza / TAPPE_MIN
            dillo(f"Una tappa può essere larga da {minima:.2f} a {massima:.2f}.")
            larghezza = dgt(prompt=f"Larghezza? invio={minima:.2f}> ", kind="f", fmin=minima, fmax=massima, default=minima)
            if larghezza <= 0:
                continue
            tappe = max(TAPPE_MIN, min(TAPPE_MAX, round(ampiezza / larghezza)))
        passo = (ob - vi) / tappe
        print(f"Risultano {tappe} tappe.")
        print(f"Una ogni {passo:+.2f} di valore.")
        # L'elenco sta qui, dove serve a decidere, e non piu' in fondo alla
        # barra, dove arrivava quando ormai non c'era piu' niente da scegliere.
        for k in range(1, tappe + 1):
            coda = ", il traguardo" if k == tappe else ""
            print(f"Tappa {k}, {vi + (ob - vi) * k / tappe:+.2f}{coda}")
        if enter_escape(prompt="Va bene? invio sì, escape no> "):
            RiproduciEffetto("roger_cw_conferma")
            return tappe
        print("Riprendiamo da capo.")


def Inizializzazione():
    """Crea un obiettivo nuovo chiedendo tutto il necessario."""
    prjnome = dgt(prompt="Nome del progetto? ", kind="s", smin=5, smax=20).title()
    prjdesc = dgt(prompt="Descrizione del progetto? ", kind="s", smin=0, smax=1024)
    print("Inserisci la data in cui inizia l'arco temporale.")
    while True:
        datainizio = DigitaData()
        if datainizio <= dt.datetime.now():
            break
        dillo("Attenzione: la data di inizio è nel futuro. I valori registrati da oggi risulterebbero anteriori all'inizio del progetto.")
        if enter_escape(prompt="La tengo così? invio sì, escape no> "):
            break
    print("Molto bene, ora inserisci la data in cui prevedi di terminarlo.")
    while True:
        datafine = DigitaData()
        if datafine > datainizio:
            break
        RiproduciEffetto("rifiuto")
        dillo("La data di fine deve essere successiva a quella di inizio. Riprova.")
    valore = dgt(prompt="Inserisci il valore di partenza:> ", kind="f", fmin=VALORE_MIN, fmax=VALORE_MAX)
    valori = {datainizio: [valore, ""]}
    while True:
        obiettivo = dgt(prompt="Inserisci l'obiettivo da raggiungere:> ", kind="f", fmin=VALORE_MIN, fmax=VALORE_MAX)
        if obiettivo != valore:
            break
        RiproduciEffetto("rifiuto")
        dillo("L'obiettivo non può essere uguale al valore di partenza. Riprova.")
    stato = {
        "prjnome": prjnome,
        "prjdesc": prjdesc,
        "datainizio": datainizio,
        "datafine": datafine,
        "valori": valori,
        "obiettivo": obiettivo,
        "tappe": None,
    }
    stato["tappe"] = ConfiguraTappe(stato)
    if stato["tappe"] is None:
        stato["tappe"] = TAPPE_PREDEFINITE
        dillo(f"Nessuna scelta: uso {TAPPE_PREDEFINITE} tappe. Le puoi rivedere dal comando tappe.")
    return stato


def _id_libero(progetti):
    """Il primo identificativo di obiettivo ancora libero, None se sono tutti occupati."""
    for i in range(MAX_PROGETTI):
        if str(i) not in progetti:
            return str(i)
    return None


def Reset(progetti):
    """Cancella tutti gli obiettivi e ne apre uno nuovo, dopo conferma esplicita.

    Restituisce l'identificativo del nuovo obiettivo, None se non si e' fatto
    niente. Il dizionario viene svuotato sul posto e non sostituito: chi lo
    ha passato, cioe' main, deve continuare a vedere lo stesso archivio,
    altrimenti un Control C dopo il reset salverebbe quello vecchio.
    """
    dillo("ATTENZIONE! Sei sicuro di voler cancellare TUTTI i progetti? L'operazione è irreversibile!")
    attesa = dgt(prompt="Digita 'sicuro'> ", kind="s", smin=0, smax=12, default="n")
    if attesa != "sicuro":
        print("Non tocco nulla.")
        return None
    RiproduciEffetto("cancellato")
    nuovo = Inizializzazione()
    progetti.clear()
    progetti["0"] = nuovo
    return "0"


def Humanize(d):
    """Una data scritta per esteso, come la direbbe una persona."""
    giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    mesi = [
        "gennaio",
        "febbraio",
        "marzo",
        "aprile",
        "maggio",
        "giugno",
        "luglio",
        "agosto",
        "settembre",
        "ottobre",
        "novembre",
        "dicembre",
    ]
    return f"{giorni[d.weekday()]} {d.day} {mesi[d.month - 1]} {d.year}, ore {d.hour:02d}:{d.minute:02d}"


def StampaTabellino(valore_iniziale, valore_attuale, valore_ideale, obiettivo):
    """I quattro valori in scala, ciascuno con il suo nome accanto.

    Prima venivano stampati soltanto ordinati, e chi ascolta lo screen reader
    non aveva modo di sapere quale numero fosse quale.
    """
    coppie = sorted(
        [(valore_iniziale, "partenza"), (valore_attuale, "attuale"), (valore_ideale, "ideale"), (obiettivo, "obiettivo")],
        key=lambda c: c[0],
    )
    # Due grandezze possono coincidere, per esempio quando il valore
    # raggiunge l'obiettivo: vanno nominate tutte e due, non una sola.
    gruppi = []
    for valore, nome in coppie:
        if gruppi and gruppi[-1][0] == valore:
            gruppi[-1][1].append(nome)
        else:
            gruppi.append((valore, [nome]))
    print("Tabellino di marcia, in scala:")
    for i, (valore, nomi) in enumerate(gruppi):
        print(f"{' e '.join(nomi)}: {valore:+.2f}")
        if i < len(gruppi) - 1:
            print(f"distanza {gruppi[i + 1][0] - valore:+.2f}")


def VPTempo(stato, show=False):
    """La percentuale di tempo trascorsa dall'inizio del progetto."""
    datainizio = stato["datainizio"]
    datafine = stato["datafine"]
    durata = datafine - datainizio
    if show:
        RiproduciEffetto("mostra")
        print("Progressi sulla linea del tempo.")
        print(f"Inizio: {Humanize(datainizio)}")
        print(f"Fine: {Humanize(datafine)}")
        print(f"Durata: {durata.days} giorni")
    oggi = dt.datetime.now().replace(microsecond=0)
    d1 = datainizio.timestamp()
    d2 = datafine.timestamp()
    percentuale_tempo = 100.0 if d2 == d1 else (oggi.timestamp() - d1) * 100 / (d2 - d1)
    if show:
        giorni_trascorsi = (oggi - datainizio).days
        frazione = frac(giorni_trascorsi, durata.days) if durata.days > 0 else "1/1"
        print(f"Oggi: {Humanize(oggi)}")
        print(f"Giorno {giorni_trascorsi} di {durata.days}")
        print(f"Tempo trascorso: {percentuale_tempo:+.2f}%")
        print(f"In frazione: {frazione}")
    return percentuale_tempo


def VPObiettivo(stato, show=False):
    """La percentuale di obiettivo raggiunta rispetto al valore di partenza."""
    valori = stato["valori"]
    obiettivo = stato["obiettivo"]
    if show:
        RiproduciEffetto("mostra")
        print("Progressi rispetto all'obiettivo.")
    if not valori:
        if show:
            print("Nessun valore registrato.")
        return 0.0
    valoreiniziale = ValoreIniziale(stato)
    valoreattuale = ValoreAttuale(stato)
    diff_obiettivo = obiettivo - valoreiniziale
    if diff_obiettivo == 0:
        percentuale_obiettivo = 100.0
    else:
        percentuale_obiettivo = (valoreattuale - valoreiniziale) * 100 / diff_obiettivo
    if show:
        print(f"Valore iniziale: {valoreiniziale:+.2f}")
        print(f"Valore attuale: {valoreattuale:+.2f}")
        print(f"Obiettivo: {obiettivo:+.2f}")
        print(f"Da coprire in tutto: {diff_obiettivo:+.2f}")
        ottenuto = valoreattuale - valoreiniziale
        frazione = frac(ottenuto / diff_obiettivo).limit_denominator() if diff_obiettivo != 0 else "1/1"
        print(f"Ottenuto: {ottenuto:+.2f}")
        print(f"Pari al {percentuale_obiettivo:+.2f}%")
        print(f"In frazione: {frazione}")
        dafare = obiettivo - valoreattuale
        perc_dafare = dafare * 100 / diff_obiettivo if diff_obiettivo != 0 else 0.0
        print(f"Da fare: {dafare:+.2f}")
        print(f"Pari al {perc_dafare:+.2f}%")
    return percentuale_obiettivo


def CalcolaProiezione(valori, obiettivo, n_punti=None):
    """La data stimata del traguardo e la velocità al giorno.

    Restituisce la coppia data, velocita'. La data e' None quando i dati non
    bastano, quando l'andamento non punta all'obiettivo e quando il traguardo
    cadrebbe oltre l'orizzonte di cento anni: con i valori in stallo la
    pendenza e' quasi zero e il conto produceva numeri che facevano fallire
    la costruzione della data con OverflowError.
    """
    date_ordinate = sorted(valori)
    if n_punti is not None:
        date_ordinate = date_ordinate[-n_punti:]
    if len(date_ordinate) < 2:
        return None, None
    if (date_ordinate[-1] - date_ordinate[0]).total_seconds() < SPAN_MINIMO_PROIEZIONE:
        return None, None
    # I timestamp assoluti sono numeri intorno al miliardo e mezzo su un
    # intervallo di pochi milioni: sottrarre il primo istante non cambia la
    # pendenza e toglie il malcondizionamento della regressione.
    origine = date_ordinate[0].timestamp()
    x = [d.timestamp() - origine for d in date_ordinate]
    y = [valori[d][0] for d in date_ordinate]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pendenza, _ = np.polyfit(x, y, 1)
    except (ValueError, TypeError, np.linalg.LinAlgError):
        return None, None
    pendenza = float(pendenza)
    if pendenza == 0:
        return None, 0.0
    velocita_giornaliera = pendenza * 86400
    secondi_mancanti = (obiettivo - y[-1]) / pendenza
    if secondi_mancanti <= 0 or secondi_mancanti > ORIZZONTE_PROIEZIONE_GIORNI * 86400:
        return None, velocita_giornaliera
    try:
        return date_ordinate[-1] + dt.timedelta(seconds=secondi_mancanti), velocita_giornaliera
    except (OverflowError, OSError, ValueError):
        return None, velocita_giornaliera


def StampaProiezioni(valori, obiettivo, valore_iniziale):
    """Le due proiezioni, quella su tutti i dati e quella sugli ultimi.

    Stava scritta identica in Nuovodato e in Infostatistiche.
    valore_iniziale serve solo a distinguere l'obiettivo gia' raggiunto
    dall'andamento che va nella direzione sbagliata: in tutti e due i casi
    non c'e' una data da stimare, ma le due cose non si somigliano affatto.
    """
    direzione = obiettivo - valore_iniziale
    ultimo = valori[max(valori)][0] if valori else valore_iniziale
    raggiunto = direzione == 0 or (obiettivo - ultimo) * direzione <= 0
    viste = (("storica, su tutti i dati", None), (f"recente, sugli ultimi {PUNTI_PROIEZIONE_RECENTE} dati", PUNTI_PROIEZIONE_RECENTE))
    for etichetta, punti in viste:
        data, velocita = CalcolaProiezione(valori, obiettivo, n_punti=punti)
        print(f"Proiezione {etichetta}:")
        if data:
            print(f"Traguardo il {Humanize(data)}")
            print(f"Velocità {velocita:+.2f} al giorno")
        elif velocita is not None:
            print("Obiettivo già raggiunto." if raggiunto else "Di questo passo non si arriva.")
            print(f"Velocità {velocita:+.2f} al giorno")
        else:
            print("Dati insufficienti o troppo ravvicinati:")
            print("servono 2 valori a un giorno di distanza.")


def RigheRegistro(valori):
    """Le righe del registro, numerate e con la differenza dal record precedente.

    Le usano sia il comando registro sia il report finale, che prima se le
    costruivano ciascuno per conto proprio.
    """
    righe = []
    precedente = None
    for contatore, k in enumerate(sorted(valori), start=1):
        v, commento = valori[k][0], valori[k][1] if len(valori[k]) > 1 else ""
        suff_commento = f" | {commento}" if commento else ""
        scarto = "(inizio)" if precedente is None else f"({v - precedente:+.2f})"
        righe.append(f"({contatore}) - {v:+.2f}, {scarto} - di {Humanize(k)}.{suff_commento}")
        precedente = v
    return righe


def VRegistro(stato):
    """Mostra tutti i valori registrati."""
    valori = stato["valori"]
    print("Dati presenti nel registro dei valori:")
    if not valori:
        RiproduciEffetto("rifiuto")
        print("Il registro è vuoto.")
        return
    RiproduciEffetto("lista")
    for riga in RigheRegistro(valori):
        print(riga)
    print(f"Totale {len(valori)} records registrati.")


def Cancelladato(stato):
    """Cancella un valore dal registro, cercandolo per numero."""
    valori = stato["valori"]
    if not valori:
        RiproduciEffetto("rifiuto")
        print("Il registro è vuoto.")
        return stato, False
    valore = dgt(prompt="Inserisci il valore che vuoi cancellare:> ", kind="f", fmin=VALORE_MIN, fmax=VALORE_MAX)
    ricerca = [k for k, v in valori.items() if v[0] == valore]
    if not ricerca:
        RiproduciEffetto("rifiuto")
        dillo("Non è stato trovato il valore specificato all'interno del registro.")
        return stato, False
    if len(ricerca) == 1:
        chiave = ricerca[0]
    else:
        print(f"Sono stati trovati {len(ricerca)} valori.")
        print("Digita il numero di quello da eliminare.")
        multi = {}
        for contatore, j in enumerate(sorted(ricerca), start=1):
            print(f"({contatore}) - in data - {Humanize(j)};")
            multi[contatore] = j
        scelta = dgt(prompt="Elemento da cancellare? (0 per annullare)> ", kind="i", imin=0, imax=len(multi))
        if scelta == 0:
            RiproduciEffetto("campanellino")
            return stato, False
        chiave = multi[scelta]
    if chiave == min(valori):
        RiproduciEffetto("rifiuto")
        print("Impossibile eliminare il valore iniziale.")
        return stato, False
    print(f"Trovato il valore {valore:+.2f}.")
    print(f"Registrato in data: {Humanize(chiave)}.")
    del valori[chiave]
    RiproduciEffetto("cancellato")
    print(f"Dato eliminato. Restano {len(valori)} records.")
    return stato, True


def _tappe_raggiunte(stato, valore):
    """Quante tappe copre un valore. None se l'obiettivo non ha le tappe."""
    tappe = stato.get("tappe")
    if not tappe:
        return None
    vi = ValoreIniziale(stato)
    span = stato["obiettivo"] - vi
    if span == 0:
        return None
    # L'epsilon serve al valore che cade esattamente su una tappa: senza,
    # un 8.999999999 dovuto alla virgola mobile la darebbe per non raggiunta.
    return max(0, min(tappe, int((valore - vi) / span * tappe + 1e-9)))


def _annuncia_tappe(stato, prima, dopo):
    """Dice e suona il passaggio di una tappa, quando ce n'e' stato uno."""
    if prima is None or dopo is None or prima == dopo:
        return
    if dopo > prima:
        RiproduciEffetto("jingle_livello_superato", base_vol=0.3)
        if dopo - prima == 1:
            print(f"Tappa {dopo} raggiunta, su {stato['tappe']}!")
        else:
            print(f"Superate {dopo - prima} tappe in un colpo,")
            print(f"dalla {prima + 1} alla {dopo}.")
    else:
        RiproduciEffetto("spirale_discendente")
        if dopo == 0:
            print("Sei sceso sotto la prima tappa.")
        else:
            print(f"Sei tornato indietro alla tappa {dopo}.")


def _parse_nuovo_input(raw):
    """Analizza l'input del comando nuovo, cioè valore seguito da un commento facoltativo.

    Accetta sia la virgola sia il punto come separatore decimale.
    Restituisce la coppia valore, commento oppure solleva ValueError.
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("non hai scritto niente")
    parti = raw.split(" ", 1)
    try:
        valore = float(parti[0].replace(",", "."))
    except ValueError as e:
        raise ValueError(f"{parti[0]} non è un numero") from e
    if not VALORE_MIN <= valore <= VALORE_MAX:
        raise ValueError(f"il valore deve stare fra {VALORE_MIN:.0f} e {VALORE_MAX:.0f}")
    commento = parti[1].strip()[:70] if len(parti) > 1 else ""
    return valore, commento


def Nuovodato(stato):
    """Registra un valore nuovo e commenta come si colloca. Restituisce stato e conclusione."""
    valori = stato["valori"]
    raw = dgt(prompt="Nuovo: valore [commento]> ", kind="s", smin=0, smax=90)
    if not raw.strip():
        print("Nessun valore inserito.")
        return stato, False, False
    try:
        valore, commento = _parse_nuovo_input(raw)
    except ValueError as e:
        RiproduciEffetto("rifiuto")
        print(f"Formato non valido: {e}.")
        return stato, False, False
    RiproduciEffetto("convalida0")
    listavalori = [v[0] for v in valori.values()]
    if listavalori:
        massimo = max(listavalori)
        minimo = min(listavalori)
        if valore > massimo:
            RiproduciEffetto("vittoria", base_vol=0.2)
            print(f"Nuovo record: {valore:+.2f}")
            print(f"Supera il massimo {massimo:+.2f}")
            print(f"di {valore - massimo:.2f}.")
        elif valore < minimo:
            RiproduciEffetto("rifiutato")
            print(f"Nuovo record: {valore:+.2f}")
            print(f"Scende sotto il minimo {minimo:+.2f}")
            print(f"di {minimo - valore:.2f}.")
        else:
            RiproduciEffetto("controllo_ok")
            print(f"Valore {valore:+.2f}, nell'intervallo noto.")
            print(f"Dal minimo {minimo:+.2f} dista {valore - minimo:+.2f}")
            print(f"Dal massimo {massimo:+.2f} dista {massimo - valore:+.2f}")
    tappe_prima = _tappe_raggiunte(stato, ValoreAttuale(stato))
    adesso = dt.datetime.now().replace(microsecond=0)
    # Due valori nello stesso secondo avrebbero la stessa chiave e uno dei
    # due sparirebbe in silenzio, in memoria e poi nel file.
    while adesso in valori:
        adesso += dt.timedelta(seconds=1)
    valori[adesso] = [valore, commento]
    print(f"Fatto. Ora il registro ha {len(valori)} records.")
    _annuncia_tappe(stato, tappe_prima, _tappe_raggiunte(stato, valore))
    valoreiniziale = ValoreIniziale(stato)
    obiettivo = stato["obiettivo"]
    durata_totale = (stato["datafine"] - stato["datainizio"]).total_seconds()
    tempo_trascorso = (adesso - stato["datainizio"]).total_seconds()
    if durata_totale > 0:
        valore_ideale = valoreiniziale + (obiettivo - valoreiniziale) * (tempo_trascorso / durata_totale)
    else:
        valore_ideale = obiettivo
    diff_ideale = valore - valore_ideale
    # La deviazione si misura sull'ampiezza dell'obiettivo, che e' la
    # grandezza rispetto a cui un ritardo significa qualcosa. Dividere per il
    # valore ideale, come si faceva prima, faceva sembrare trascurabile
    # mezzo chilo su cinque da perdere.
    ampiezza = abs(obiettivo - valoreiniziale)
    perc_diff_ideale = (diff_ideale / ampiezza) * 100 if ampiezza else 0.0
    if abs(diff_ideale) < 0.01:
        RiproduciEffetto("in_linea_ideale")
        giudizio = None
    elif diff_ideale < 0:
        RiproduciEffetto("discesa_ideale")
        giudizio = "inferiore"
    else:
        RiproduciEffetto("salita_ideale")
        giudizio = "superiore"
    print(f"Valore ideale di oggi: {valore_ideale:+.2f}")
    if giudizio is None:
        print("Sei esattamente in pari con la tabella.")
    else:
        print(f"Il valore inserito è {giudizio}")
        print(f"di {abs(diff_ideale):.2f}.")
        print(f"Deviazione {perc_diff_ideale:+.2f}% sull'obiettivo.")
    StampaTabellino(valoreiniziale, valore, valore_ideale, obiettivo)
    StampaProiezioni(valori, obiettivo, valoreiniziale)
    percentuale_obiettivo = VPObiettivo(stato)
    percentuale_tempo = VPTempo(stato)
    concluso = percentuale_obiettivo >= 100 or percentuale_tempo >= 100
    return stato, True, concluso


def VMenu():
    """Mostra l'elenco dei comandi."""
    print(f"Menù di QUINQU, versione {APP_VERSION}.")
    menu(d=main_menu, show_only=True)


def SelezionaProgetto(progetti):
    """Fa scegliere l'obiettivo su cui lavorare e ne restituisce l'identificativo."""
    opzioni = {}
    for pid, p in progetti.items():
        perc_ob = VPObiettivo(p, show=False)
        perc_t = VPTempo(p, show=False)
        opzioni[pid] = f"{p['prjnome']} ({len(p['valori'])} dati) [Obiettivo: {perc_ob:.1f}%, Tempo: {perc_t:.1f}%] > {p['prjdesc']}"
    if _id_libero(progetti) is not None:
        opzioni["n"] = "-- Crea Nuovo Obiettivo --"
    RiproduciEffetto("lista")
    print("Obiettivi disponibili:")
    while True:
        scelta = menu(d=opzioni, p="Scegli obiettivo: ", show=True, keyslist=True)
        if scelta is None:
            if progetti:
                print("Selezione annullata.")
                return next(iter(progetti))
            continue
        if scelta == "n":
            nuovo_id = _id_libero(progetti)
            if nuovo_id is None:
                RiproduciEffetto("rifiuto")
                print(f"Massimo {MAX_PROGETTI} obiettivi raggiunto.")
                continue
            progetti[nuovo_id] = Inizializzazione()
            return nuovo_id
        return scelta


def Cambiafine(stato):
    """Sposta la data di fine progetto."""
    print("Vecchia data di fine progetto:")
    print(Humanize(stato["datafine"]))
    print("Nuova data di fine progetto...")
    while True:
        nuova_data = DigitaData()
        if nuova_data > stato["datainizio"]:
            stato["datafine"] = nuova_data
            RiproduciEffetto("roger_cw_conferma")
            return stato
        RiproduciEffetto("rifiuto")
        dillo("La data di fine deve essere successiva a quella di inizio. Riprova.")


def VConfronto(stato):
    """Mette a confronto la percentuale di tempo e quella di obiettivo."""
    if not stato["valori"]:
        RiproduciEffetto("rifiuto")
        print("Dati insufficienti per un confronto.")
        return
    op = VPObiettivo(stato)
    ot = VPTempo(stato)
    scarto = ot - op
    if abs(scarto) <= TOLLERANZA_CONFRONTO:
        giudizio = "progressione uniforme, molto bene!"
        RiproduciEffetto("controllo_ok")
    elif ot < op - TOLLERANZA_CONFRONTO:
        giudizio = "variazione troppo rapida, rallentare."
        RiproduciEffetto("campanellino")
    else:
        giudizio = "variazione troppo lenta, accelerare."
        RiproduciEffetto("rifiutato")
    print(f"Tempo: {ot:+.2f}%")
    print(f"Valore: {op:+.2f}%")
    if scarto > 0:
        print(f"Il tempo è avanti di {scarto:.2f}%")
    elif scarto < 0:
        print(f"Il valore è avanti di {-scarto:.2f}%")
    else:
        print("Tempo e valore sono in pari.")
    dillo(giudizio)


def _lunghezza_barra(tappe):
    """Quante celle deve avere la barra perché le tappe non si tocchino."""
    return max(LARGHEZZA_RIGA, tappe * CELLE_PER_TAPPA)


def _cella(frazione, lunghezza):
    """L'indice di cella, da 0 all'ultima, per una frazione di percorso."""
    f = max(0.0, min(1.0, frazione))
    return round(f * (lunghezza - 1))


def DisegnaBarra(frazione_piena, marcatori, lunghezza):
    """Le righe della barra, già tagliate a LARGHEZZA_RIGA caratteri.

    marcatori e' una lista di terne cella, etichetta, ordine. Quando piu'
    marcatori cadono nella stessa cella le etichette si scrivono unite, in
    quell'ordine, e la cella occupa piu' di un carattere: e' il motivo per
    cui la barra non ha piu' lunghezza fissa. Cosi' nessun marcatore resta
    nascosto e non serve nessun carattere speciale per dire che due cose si
    incontrano.
    """
    pieno = max(0.0, min(1.0, frazione_piena)) * lunghezza
    intere = int(pieno)
    resto = pieno - intere
    celle = []
    for i in range(lunghezza):
        if i < intere:
            celle.append(GRADAZIONI[-1])
        elif i == intere:
            celle.append(GRADAZIONI[int(resto * (len(GRADAZIONI) - 1))])
        else:
            celle.append(GRADAZIONI[0])
    insieme = {}
    for cella, etichetta, _ordine in sorted(marcatori, key=lambda m: (m[0], m[2])):
        insieme.setdefault(cella, []).append(etichetta)
    for cella, etichette in insieme.items():
        celle[cella] = "".join(etichette)
    righe = []
    corrente = ""
    for pezzo in celle:
        if corrente and len(corrente) + len(pezzo) > LARGHEZZA_RIGA:
            righe.append(corrente)
            corrente = pezzo
        else:
            corrente += pezzo
    if corrente:
        righe.append(corrente)
    return righe


def _abilita_ansi():
    """Accende su Windows l'interpretazione delle sequenze ANSI. Vero se riuscita.

    Serve solo a riportare il cursore all'inizio della barra: se non si
    riesce, si rinuncia allo spostamento e non si stampa nessuna sequenza,
    perche' una sequenza non interpretata finirebbe letta dallo screen reader.
    """
    if os.name != "nt":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        maniglia = kernel32.GetStdHandle(-11)
        modo = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(maniglia, ctypes.byref(modo)):
            return False
        return bool(kernel32.SetConsoleMode(maniglia, modo.value | 0x0004))
    except (OSError, AttributeError, ValueError):
        return False


def StampaBarraBraille(righe):
    """Stampa la barra e aspetta in silenzio, con il cursore sulla barra.

    Il display braille segue il cursore della console. Stampando le righe
    e basta, il cursore finiva sulla riga vuota sotto la barra e sotto le
    dita non arrivava niente: qui si risale fino alla prima riga della
    barra, si aspetta un tasto qualsiasi e poi si torna giu' per non
    scrivere sopra a quello che si e' appena disegnato.
    """
    if not righe:
        return
    ansi = _abilita_ansi()
    ultima = len(righe) - 1
    for i, riga in enumerate(righe):
        print(f"\r{riga}", end="" if i == ultima else "\n", flush=True)
    if ansi and ultima:
        print(f"\r\033[{ultima}A", end="", flush=True)
    else:
        print("\r", end="", flush=True)
    key()
    if ansi and ultima:
        print(f"\033[{ultima}B", end="", flush=True)
    print()


def _riga_marcatore(lettera, nome, frazione, coda, lunghezza):
    """Una riga di legenda: lettera, cosa indica, in quale cella e con quale valore."""
    testo = f"{lettera} {nome}, cella {_cella(frazione, lunghezza) + 1}, {coda}"
    if frazione < 0:
        testo += ", prima dell'inizio"
    elif frazione > 1:
        testo += ", oltre il traguardo"
    return testo


def RaccontaSituazione(stato, misure):
    """La stessa situazione della barra, ma raccontata a parole.

    La barra e' fatta per chi legge sul display braille. Chi non ce l'ha
    deve poter sapere lo stesso a che punto sta, senza contare i caratteri:
    fra quali tappe si trova, di quanto ha superato l'ultima e quanto gli
    manca alla prossima.
    misure e' il dizionario delle grandezze gia' calcolate da MostraTappe,
    con le chiavi vi, ob, attuale, f_attuale, f_tempo, ideale, tappe,
    valori_tappe, raggiunte, minimo, massimo e media.
    """
    vi = misure["vi"]
    ob = misure["ob"]
    attuale = misure["attuale"]
    f_attuale = misure["f_attuale"]
    f_tempo = misure["f_tempo"]
    tappe = misure["tappe"]
    valori_tappe = misure["valori_tappe"]
    raggiunte = misure["raggiunte"]
    print(f"Situazione di {stato['prjnome']}.")
    print(f"Si va da {vi:+.2f} a {ob:+.2f}.")
    print(f"Sei a {attuale:+.2f}.")
    print(f"Percorso coperto: {f_attuale * 100:.2f}%.")
    print(f"Tempo trascorso: {f_tempo * 100:.2f}%.")
    print(f"Valore giusto adesso: {misure['ideale']:+.2f}.")
    scarto = (f_attuale - f_tempo) * 100
    if abs(scarto) < 0.005:
        print("Sei esattamente in pari con il tempo.")
    else:
        verso = "avanti" if scarto > 0 else "indietro"
        print(f"Sei {verso} sul tempo di {abs(scarto):.2f} punti,")
        print(f"cioè di {abs(attuale - misure['ideale']):.2f} di valore.")
    print(f"Tappe: {tappe}, una ogni {(ob - vi) / tappe:+.2f}.")
    if f_attuale < 0:
        dillo(f"Sei tornato indietro rispetto alla partenza di {abs(attuale - vi):.2f}.")
        print(f"Tappa 1, {valori_tappe[0]:+.2f}, mancano {abs(valori_tappe[0] - attuale):.2f}.")
    elif raggiunte == 0:
        print("Non hai ancora raggiunto la prima tappa.")
        print(f"Dalla partenza ti sei mosso di {abs(attuale - vi):.2f}.")
        print(f"Tappa 1, {valori_tappe[0]:+.2f}, mancano {abs(valori_tappe[0] - attuale):.2f}.")
        print(f"Avanzamento nella tappa 1: {f_attuale * tappe * 100:.2f}%.")
    elif raggiunte >= tappe:
        print(f"Hai superato tutte le {tappe} tappe.")
        oltre = abs(attuale - ob)
        if oltre < 0.005:
            print(f"Sei esattamente sul traguardo, {ob:+.2f}.")
        else:
            print(f"Traguardo {ob:+.2f}, passato di {oltre:.2f}.")
    else:
        superata = valori_tappe[raggiunte - 1]
        prossima = valori_tappe[raggiunte]
        print(f"Sei fra la tappa {raggiunte} e la {raggiunte + 1}.")
        print(f"Tappa {raggiunte}, {superata:+.2f}, superata di {abs(attuale - superata):.2f}.")
        print(f"Tappa {raggiunte + 1}, {prossima:+.2f}, mancano {abs(prossima - attuale):.2f}.")
        fatta = (f_attuale * tappe - raggiunte) * 100
        print(f"Avanzamento nella tappa {raggiunte + 1}: {fatta:.2f}%.")
    print(f"Minimo {misure['minimo']:+.2f}, massimo {misure['massimo']:+.2f}.")
    print(f"Media {misure['media']:+.2f} su {len(stato['valori'])} valori.")


def MostraTappe(stato):
    """La barra delle tappe, con la legenda di ogni marcatore.

    Restituisce True se le tappe sono state riviste e c'è da salvare.
    """
    valori = stato["valori"]
    if not valori:
        RiproduciEffetto("rifiuto")
        print("Il registro è vuoto.")
        return False
    vi = ValoreIniziale(stato)
    ob = stato["obiettivo"]
    span = ob - vi
    if span == 0:
        RiproduciEffetto("rifiuto")
        print("Valore iniziale e obiettivo coincidono:")
        print("non c'è nessuna scala da disegnare.")
        return False
    cambiato = False
    if not stato.get("tappe"):
        print("Questo obiettivo non ha ancora le tappe.")
        scelta = ConfiguraTappe(stato)
        if scelta is None:
            print("Tappe non impostate.")
            return False
        stato["tappe"] = scelta
        cambiato = True
    tappe = stato["tappe"]
    numeri = [v[0] for v in valori.values()]
    attuale = ValoreAttuale(stato)
    minimo, massimo = min(numeri), max(numeri)
    media = statistics.fmean(numeri)
    lunghezza = _lunghezza_barra(tappe)
    f_attuale = (attuale - vi) / span
    f_tempo = VPTempo(stato) / 100.0
    ideale = vi + span * max(0.0, min(1.0, f_tempo))
    f_min = (minimo - vi) / span
    f_max = (massimo - vi) / span
    f_media = (media - vi) / span
    # Il terzo campo e' l'ordine con cui le etichette si scrivono quando due
    # o piu' marcatori finiscono nella stessa cella. Il numero della tappa
    # viene sempre per primo, poi le lettere.
    marcatori = [(0, "I", 1), (lunghezza - 1, "F", 1)]
    marcatori.append((_cella(f_attuale, lunghezza), "O", 2))
    marcatori.append((_cella(f_tempo, lunghezza), "T", 3))
    valori_tappe = []
    for k in range(1, tappe + 1):
        valori_tappe.append(vi + span * k / tappe)
        marcatori.append((_cella(k / tappe, lunghezza), str(k), 0))
    marcatori.append((_cella(f_media, lunghezza), "D", 4))
    marcatori.append((_cella(f_max, lunghezza), "X", 5))
    marcatori.append((_cella(f_min, lunghezza), "M", 6))
    righe_barra = DisegnaBarra(f_attuale, marcatori, lunghezza)
    raggiunte = 0
    for k in range(1, tappe + 1):
        if f_attuale >= k / tappe:
            raggiunte = k
    RiproduciEffetto("mostra")
    RaccontaSituazione(
        stato,
        {
            "vi": vi,
            "ob": ob,
            "attuale": attuale,
            "f_attuale": f_attuale,
            "f_tempo": f_tempo,
            "ideale": ideale,
            "tappe": tappe,
            "valori_tappe": valori_tappe,
            "raggiunte": raggiunte,
            "minimo": minimo,
            "massimo": massimo,
            "media": media,
        },
    )
    # La legenda dice soltanto dove sta ogni lettera: i valori li ha gia'
    # detti il racconto qui sopra, e ripeterli era un doppione. Sta prima
    # della barra, e in righe intere: sono spiegazioni da leggere, non
    # simboli da toccare, quindi non vanno spezzate ogni quaranta caratteri.
    voci = [("I", 0.0), ("F", 1.0), ("O", f_attuale), ("T", f_tempo), ("D", f_media), ("X", f_max), ("M", f_min)]
    pezzi = []
    for lettera, frazione in voci:
        nota = ""
        if frazione < 0:
            nota = " prima dell'inizio"
        elif frazione > 1:
            nota = " oltre il traguardo"
        pezzi.append(f"{lettera} cella {_cella(frazione, lunghezza) + 1}{nota}")
    print("Nella barra: " + ", ".join(pezzi) + ".")
    print("Dove due o più marcatori cadono nella stessa cella, la barra li scrive uniti, prima il numero della tappa e poi le lettere.")
    print(f"Barra: {lunghezza} celle su {len(righe_barra)} righe da {LARGHEZZA_RIGA}.")
    StampaBarraBraille(righe_barra)
    return cambiato


def ModificaTappe(stato):
    """Rivede in quante tappe è diviso l'obiettivo. Vero se è cambiato qualcosa."""
    if not stato["valori"]:
        RiproduciEffetto("rifiuto")
        print("Il registro è vuoto.")
        return False
    attuali = stato.get("tappe")
    if attuali:
        print(f"Adesso l'obiettivo è diviso in {attuali} tappe.")
    else:
        print("L'obiettivo non ha ancora le tappe.")
    scelta = ConfiguraTappe(stato)
    if scelta is None:
        RiproduciEffetto("campanellino")
        print("Niente cambiato.")
        return False
    stato["tappe"] = scelta
    print(f"Ora le tappe sono {scelta}.")
    return True


def _volte(quante):
    """Volta o volte, perché una sola non sono volte."""
    return "volta" if quante == 1 else "volte"


def Infostatistiche(stato, annuncia=True):
    """Tutte le statistiche sui valori registrati."""
    valori = stato["valori"]
    obiettivo = stato["obiettivo"]
    if len(valori) < MINIMO_VALORI_STATISTICHE:
        if annuncia:
            RiproduciEffetto("rifiuto")
        dillo(f"Sono stati registrati pochi valori per mostrare le statistiche, ne servono almeno {MINIMO_VALORI_STATISTICHE}.")
        return
    if annuncia:
        RiproduciEffetto("mostra")
    print("Informazioni statistiche sui valori.")
    lista_valori = [v[0] for v in valori.values()]
    print(f"Numero di records: {len(lista_valori)}")
    piupiccolo = min(lista_valori)
    piugrande = max(lista_valori)
    listapiccoli = [k for k, v in valori.items() if v[0] == piupiccolo]
    listagrandi = [k for k, v in valori.items() if v[0] == piugrande]
    print(f"Valore massimo {piugrande:+.2f}, {len(listagrandi)} {_volte(len(listagrandi))}.")
    for j in sorted(listagrandi):
        print(f"In data: {Humanize(j)};")
    print(f"Valore minimo {piupiccolo:+.2f}, {len(listapiccoli)} {_volte(len(listapiccoli))}.")
    for j in sorted(listapiccoli):
        print(f"In data: {Humanize(j)};")
    print(f"Media aritmetica: {statistics.fmean(lista_valori):+.2f}")
    print(f"Mediana bassa: {statistics.median_low(lista_valori):+.2f}")
    print(f"Mediana: {statistics.median(lista_valori):+.2f}")
    print(f"Mediana alta: {statistics.median_high(lista_valori):+.2f}")
    print(f"Moda: {statistics.mode(lista_valori):+.2f}")
    print(f"Deviazione standard: {statistics.stdev(lista_valori):+.2f}")
    print(f"Varianza: {statistics.variance(lista_valori):+.2f}")
    _stampa_quartili(sorted(valori.items(), key=lambda x: x[1][0]), "per valore")
    _stampa_quartili(sorted(valori.items()), "per tempo")
    date_ordinate = sorted(valori)
    primo_valore = valori[date_ordinate[0]][0]
    ultimo_valore = valori[date_ordinate[-1]][0]
    print(f"Variazione totale: {ultimo_valore - primo_valore:+.2f}")
    salti = []
    aumenti = 0
    cali = 0
    tempi_tra_inserimenti = []
    for precedente, corrente in itertools.pairwise(date_ordinate):
        delta_val = valori[corrente][0] - valori[precedente][0]
        salti.append((delta_val, corrente))
        tempi_tra_inserimenti.append((corrente - precedente).total_seconds())
        if delta_val > 0:
            aumenti += 1
        elif delta_val < 0:
            cali += 1
    if salti:
        salto_max = max(salti, key=lambda x: x[0])
        salto_min = min(salti, key=lambda x: x[0])
        print(f"Passaggi: {aumenti} in aumento, {cali} in calo,")
        print(f"{len(salti) - aumenti - cali} stabili.")
        if salto_max[0] > 0:
            print(f"Picco di aumento: {salto_max[0]:+.2f}")
            print(f"In data {Humanize(salto_max[1])}.")
        if salto_min[0] < 0:
            print(f"Picco di calo: {salto_min[0]:+.2f}")
            print(f"In data {Humanize(salto_min[1])}.")
        print(f"Variazione media per passo: {statistics.fmean([x[0] for x in salti]):+.2f}")
        media_tempo_sec = statistics.fmean(tempi_tra_inserimenti)
        giorni_media = int(media_tempo_sec // 86400)
        ore_media = int((media_tempo_sec % 86400) // 3600)
        print(f"Un inserimento ogni {giorni_media} giorni")
        print(f"e {ore_media} ore.")
    StampaProiezioni(valori, obiettivo, primo_valore)
    oggi = dt.datetime.now().replace(microsecond=0)
    giorni_rimanenti = (stato["datafine"] - oggi).total_seconds() / 86400
    da_fare_oggi = obiettivo - ultimo_valore
    if giorni_rimanenti > 0 and da_fare_oggi != 0:
        print("Tabella di marcia: occorre acquisire")
        print(f"{da_fare_oggi / giorni_rimanenti:+.2f} al giorno.")
    elif giorni_rimanenti <= 0 and da_fare_oggi != 0:
        dillo("Tempo scaduto: non c'è più un progresso giornaliero da calcolare.")


def _stampa_quartili(dati_ordinati, etichetta):
    """I quattro quarti di una serie già ordinata, con estremi e media di ciascuno."""
    print(f"Suddivisione in quartili {etichetta}:")
    for idx, gruppo in enumerate(np.array_split(range(len(dati_ordinati)), 4), 1):
        chunk = [dati_ordinati[i] for i in gruppo]
        if not chunk:
            continue
        chunk_vals = [item[1][0] for item in chunk]
        chunk_dates = [item[0] for item in chunk]
        print(f"Q{idx}, da {Humanize(min(chunk_dates))}")
        print(f"a {Humanize(max(chunk_dates))}")
        print(f"minimo {min(chunk_vals):+.2f}, media {statistics.fmean(chunk_vals):+.2f}, massimo {max(chunk_vals):+.2f}")


def _nome_file_report(prjnome):
    """Un nome di file valido per il report, che non sovrascriva niente.

    Il nome del progetto lo sceglie l'utente e puo' contenere i due punti o
    la barra, che Windows rifiuta: prima l'errore faceva perdere il report e,
    con lui, il progetto intero.
    """
    pulito = "".join("_" if c in VIETATI_NEI_NOMI or ord(c) < 32 else c for c in prjnome)
    pulito = pulito.strip().rstrip(".")
    if not pulito:
        pulito = "Progetto"
    base = os.path.join(CARTELLA, f"Quinqu-{pulito}")
    percorso = f"{base}.txt"
    contatore = 2
    while os.path.exists(percorso):
        percorso = f"{base} ({contatore}).txt"
        contatore += 1
    return percorso


def ConcludiProgetto(stato):
    """Scrive il report finale del progetto. Restituisce True solo se il file esiste davvero.

    Prima restituiva True in ogni caso, anche quando la scrittura falliva, e
    il chiamante cancellava il progetto fidandosi di quel True.
    """
    prjnome = stato["prjnome"]
    valori = stato["valori"]
    obiettivo = stato["obiettivo"]
    print("Il progetto è concluso.")
    print("Creazione del report finale...")
    RiproduciEffetto("vittoria")
    valoreiniziale = ValoreIniziale(stato) if valori else 0
    valoreattuale = ValoreAttuale(stato) if valori else 0
    diff_obiettivo = obiettivo - valoreiniziale
    percentuale_obiettivo = (valoreattuale - valoreiniziale) * 100 / diff_obiettivo if diff_obiettivo != 0 else 100.0
    oggi = dt.datetime.now().replace(microsecond=0)
    diff_tempo = stato["datafine"].timestamp() - stato["datainizio"].timestamp()
    percentuale_tempo = (oggi.timestamp() - stato["datainizio"].timestamp()) * 100 / diff_tempo if diff_tempo != 0 else 100.0
    if percentuale_obiettivo >= 100:
        esito = f"Obiettivo raggiunto nel {percentuale_tempo:.2f}% del tempo a disposizione"
    elif percentuale_tempo >= 100:
        esito = f"Tempo scaduto: raggiunto il {percentuale_obiettivo:.2f}% dell'obiettivo"
    else:
        esito = f"Progetto in corso: raggiunto il {percentuale_obiettivo:.2f}% dell'obiettivo nel {percentuale_tempo:.2f}% del tempo"
    # Il testo si compone tutto in memoria e si scrive in un colpo solo: un
    # guasto a meta' non lascia piu' un report troncato sul disco.
    righe = [
        f"Nome del progetto: {prjnome}",
        f"Descrizione: {stato['prjdesc']}",
        f"Data inizio: {Humanize(stato['datainizio'])}",
        f"Data fine: {Humanize(stato['datafine'])}",
        f"Valore iniziale: {valoreiniziale:+.2f}",
        f"Valore obiettivo: {obiettivo:+.2f}",
        esito,
        "Registro dei valori:",
    ]
    righe.extend(RigheRegistro(valori))
    raccolta = io.StringIO()
    with contextlib.redirect_stdout(raccolta):
        Infostatistiche(stato, annuncia=False)
    righe.extend(raccolta.getvalue().splitlines())
    righe.append(f"Report prodotto il {Humanize(dt.datetime.now())}")
    righe.append(f"Applicazione: Quanto In Quanto (Quinqu) versione {APP_VERSION} del {RELEASE_DATE}")
    percorso = _nome_file_report(prjnome)
    try:
        with open(percorso, "w", encoding="utf-8") as f:
            f.write("\n".join(righe) + "\n")
    except OSError as e:
        RiproduciEffetto("rifiuto")
        print(f"Errore nella creazione del report: {e}")
        return False
    print(f"Report salvato come {os.path.basename(percorso)}.")
    print(f"Progetto '{prjnome}' terminato.")
    return True


def GestisciConclusione(progetti, id_corrente):
    """Chiude il progetto arrivato in fondo e sceglie su quale continuare.

    Restituisce la coppia identificativo, prosegui. Se il report non si e'
    scritto il progetto resta dov'e': cancellarlo lo farebbe sparire e basta.
    """
    stato = progetti[id_corrente]
    if not ConcludiProgetto(stato):
        dillo("Il progetto resta nell'archivio: prima va risolto il problema del report.")
        return id_corrente, True
    prj_concluso = stato["prjnome"]
    del progetti[id_corrente]
    Salva(progetti, annuncia=False)
    if not progetti:
        print("Tutti gli obiettivi sono stati conclusi.")
        risposta = dgt(prompt="Vuoi creare un nuovo obiettivo? (S|N)> ", kind="s", smin=1, smax=1, default="s").lower()
        if risposta != "s":
            return None, False
        progetti["0"] = Inizializzazione()
        Salva(progetti, annuncia=False)
        return "0", True
    print(f"Obiettivo '{prj_concluso}' concluso.")
    if len(progetti) == 1:
        nuovo_id = next(iter(progetti))
        dillo(f"Resta un solo obiettivo attivo, '{progetti[nuovo_id]['prjnome']}', che viene caricato automaticamente.")
        return nuovo_id, True
    return SelezionaProgetto(progetti), True


def Suona(stato, chiedi_durata=False, portamento=True):
    """Riproduce l'andamento dei valori come una melodia."""
    valori = stato["valori"]
    if not valori:
        RiproduciEffetto("rifiuto")
        print("Nessun valore registrato da riprodurre.")
        return
    dati = [valori[k][0] for k in sorted(valori)]
    durata = len(dati) * 0.25
    if chiedi_durata:
        durata = dgt(prompt="Durata? ", kind="f", fmin=3.0, fmax=60.0, default=durata)
    print(f"Riproduzione di {len(dati)} valori,")
    print(f"durata {durata:.1f} secondi.")
    sonify(dati, duration=durata, ptm=portamento, vol=0.3)


def CicloComandi(progetti, id_corrente):
    """Il ciclo principale dei comandi. Restituisce quando si esce."""
    stato = progetti[id_corrente]
    print("Digita M per leggere il menù dell'App")
    while True:
        attesa = menu(d=main_menu, p="CMD> ", show=False)
        if attesa is None:
            continue
        attesa = attesa.lower()
        if attesa == "menu":
            VMenu()
        elif attesa == "esci":
            RiproduciEffetto("quinqu_shutdown")
            Salva(progetti)
            return
        elif attesa == "nuovo":
            stato, cambiato, concluso = Nuovodato(stato)
            if cambiato:
                Salva(progetti, annuncia=False)
            if concluso:
                id_corrente, prosegui = GestisciConclusione(progetti, id_corrente)
                if not prosegui:
                    return
                stato = progetti[id_corrente]
        elif attesa == "cancella":
            stato, cambiato = Cancelladato(stato)
            if cambiato:
                Salva(progetti, annuncia=False)
        elif attesa == "registro":
            VRegistro(stato)
        elif attesa == "suono_p":
            Suona(stato, portamento=True)
        elif attesa == "suono_np":
            Suona(stato, portamento=False)
        elif attesa == "suono_d":
            Suona(stato, chiedi_durata=True, portamento=True)
        elif attesa == "progresso_ob":
            VPObiettivo(stato, show=True)
        elif attesa == "progresso_t":
            VPTempo(stato, show=True)
        elif attesa == "confronto":
            VConfronto(stato)
        elif attesa == "tappe":
            if MostraTappe(stato):
                Salva(progetti, annuncia=False)
        elif attesa == "dividi":
            if ModificaTappe(stato):
                Salva(progetti, annuncia=False)
        elif attesa == "statistiche":
            Infostatistiche(stato)
        elif attesa == "fine":
            stato = Cambiafine(stato)
            Salva(progetti, annuncia=False)
        elif attesa == "obiettivo":
            print(f"Obiettivo attuale: {stato['obiettivo']:+.2f}")
            nuovo_ob = dgt(prompt="Nuovo obiettivo? > ", kind="f", fmin=VALORE_MIN, fmax=VALORE_MAX)
            if nuovo_ob != ValoreIniziale(stato):
                stato["obiettivo"] = nuovo_ob
                RiproduciEffetto("roger_cw_conferma")
                print("Nuovo obiettivo impostato.")
                Salva(progetti, annuncia=False)
            else:
                RiproduciEffetto("rifiuto")
                dillo("L'obiettivo non può coincidere con il valore iniziale.")
        elif attesa == "salva":
            Salva(progetti)
        elif attesa == "cambia":
            id_corrente = SelezionaProgetto(progetti)
            stato = progetti[id_corrente]
            Salva(progetti, annuncia=False)
            RiproduciEffetto("campanellino")
            print(f"Passato a {stato['prjnome']}.")
        elif attesa == "apri":
            nuovo_id = _id_libero(progetti)
            if nuovo_id is None:
                RiproduciEffetto("rifiuto")
                print(f"Massimo {MAX_PROGETTI} obiettivi raggiunto.")
            else:
                progetti[nuovo_id] = Inizializzazione()
                id_corrente = nuovo_id
                stato = progetti[id_corrente]
                Salva(progetti, annuncia=False)
                print(f"Creato e caricato: {stato['prjnome']}")
        elif attesa == "elimina":
            id_corrente = _elimina_corrente(progetti, id_corrente)
            stato = progetti[id_corrente]
        elif attesa == "reset":
            nuovo_id = Reset(progetti)
            if nuovo_id is not None:
                id_corrente = nuovo_id
                stato = progetti[id_corrente]
                Salva(progetti, annuncia=False)
        else:
            RiproduciEffetto("rifiuto")
            print(f"{attesa} non è un comando valido.")
            VMenu()


def _elimina_corrente(progetti, id_corrente):
    """Elimina l'obiettivo in uso e restituisce quello su cui proseguire."""
    stato = progetti[id_corrente]
    print(f"Vuoi davvero eliminare {stato['prjnome']}?")
    attesa = dgt(prompt="Digita 'sicuro'> ", kind="s", smin=0, smax=12, default="n")
    if attesa != "sicuro":
        RiproduciEffetto("campanellino")
        print("Operazione annullata.")
        return id_corrente
    RiproduciEffetto("cancellato")
    prj_eliminato = stato["prjnome"]
    del progetti[id_corrente]
    if not progetti:
        print("Tutti gli obiettivi sono stati eliminati.")
        progetti["0"] = Inizializzazione()
        nuovo_id = "0"
    elif len(progetti) == 1:
        nuovo_id = next(iter(progetti))
    else:
        nuovo_id = SelezionaProgetto(progetti)
    Salva(progetti, annuncia=False)
    print(f"Obiettivo '{prj_eliminato}' eliminato.")
    print(f"Passato a {progetti[nuovo_id]['prjnome']}.")
    return nuovo_id


def main():
    """Avvio dell'applicazione: aggiornamento, caricamento, scelta dell'obiettivo, comandi."""
    RiproduciEffetto("quinqu_startup")
    print(f"Welcome a {AUTORE}!")
    print("Applicazione: Quanto In Quanto (Quinqu)")
    print(f"Versione {APP_VERSION} del {RELEASE_DATE}")
    dillo(
        "Un'App per tenere traccia dei progressi in un obiettivo, esprimibile con un valore numerico, da raggiungere in un determinato arco temporale."
    )
    if gestisci_aggiornamento(APP_NAME, APP_VERSION, API_RELEASE):
        return
    print("Controllo la registrazione salvata...")
    progetti, errore, scartati = Carica()
    if errore:
        RiproduciEffetto("rifiuto")
        dillo(f"Non riesco a leggere l'archivio: {errore}")
        for riga in scartati:
            dillo(riga)
        dillo(f"Il file non è stato toccato: se ne trovi una copia in {RECORDNAME}.bak, prova a ripristinarla a mano.")
        print("Chiudo senza salvare nulla.")
        return
    if scartati:
        RiproduciEffetto("rifiutato")
        dillo(f"{len(scartati)} obiettivi non sono stati caricati perché malformati:")
        for riga in scartati:
            dillo(riga)
        dillo(
            f"Il file su disco è ancora intero. Se prosegui, al primo salvataggio quegli obiettivi non ci saranno più: se ti servono, fai adesso una copia di {RECORDNAME}."
        )
        if not enter_escape(prompt="Proseguo? invio sì, escape no> "):
            print("Chiudo senza salvare nulla.")
            return
    if not progetti:
        RiproduciEffetto("campanellino")
        dillo(f"{RECORDNAME} non trovato o dati cancellati. Apertura nuova registrazione.")
        progetti["0"] = Inizializzazione()
        id_corrente = "0"
        Salva(progetti)
    else:
        RiproduciEffetto("controllo_ok")
        if len(progetti) == 1:
            id_corrente = next(iter(progetti))
            print("Unico obiettivo trovato e caricato:")
            print(progetti[id_corrente]["prjnome"])
        else:
            id_corrente = SelezionaProgetto(progetti)
            Salva(progetti, annuncia=False)
    stato = progetti[id_corrente]
    if VPObiettivo(stato) >= 100 or VPTempo(stato) >= 100:
        id_corrente, prosegui = GestisciConclusione(progetti, id_corrente)
        if not prosegui:
            return
    try:
        CicloComandi(progetti, id_corrente)
    except KeyboardInterrupt:
        print()
        print("Interruzione da tastiera.")
        if Salva(progetti, annuncia=False):
            print("Archivio salvato prima di uscire.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Interrotto.")
    except Exception as e:  # noqa: BLE001
        print("Errore imprevisto, l'App si chiude.")
        print(f"{type(e).__name__}: {e}")
