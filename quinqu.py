# Quanto in Quanto (Quinqu). Data di concepimento 10/02/2024.
# Programma per seguire e salvare i progressi nel raggiungimento di un obiettivo il cui valore possa essere espresso in numeri

import os
import sys
import json
import pickle
import statistics
import datetime as dt
from fractions import Fraction as frac
from GBUtils import dgt, key, Acusticator, sonify

VERSIONE = "3.3.1 del 12 aprile 2026"
AUTORE = "Gabriele"
RECORDNAME = "quinqu.json"
OLD_RECORDNAME = "quinqu.db"

SUONO = {
    "dato": ["a5", .070, 0, .4, "c6", .070, 0, .4, "g6", .150, 0, .4],
    "sopra": ['e4', 0.035, 0, 0.4, 'p', 0.035, 0, 0.4, 'g4', 0.035, 0, 0.4, 'p', 0.035, 0, 0.4, 'b4', 0.035, 0, 0.4, 'p', 0.035, 0, 0.4],
    "mezzo": ['g4', 0.035, 0, 0.4, 'p', 0.035, 0, 0.4, 'g4', 0.035, 0, 0.4, 'p', 0.035, 0, 0.4, 'g4', 0.035, 0, 0.4, 'p', 0.035, 0, 0.4],
    "sotto": ['b4', 0.035, 0, 0.4, 'p', 0.035, 0, 0.4, 'g4', 0.035, 0, 0.4, 'p', 0.035, 0, 0.4, 'e4', 0.035, 0, 0.4],
    "startup": ["c5", 0.1, 0, 0.4, "e5", 0.1, 0, 0.4, "g5", 0.1, 0, 0.4, "c6", 0.3, 0, 0.4],
    "shutdown": ["c6", 0.1, 0, 0.4, "g5", 0.1, 0, 0.4, "e5", 0.1, 0, 0.4, "c5", 0.3, 0, 0.4],
    "save": ["g5", 0.05, 0, 0.4, "b5", 0.1, 0, 0.4],
    "delete": ["e4", 0.1, 0, 0.4, "c4", 0.2, 0, 0.4],
    "reset": ["c4", 0.1, 0, 0.4, "c3", 0.4, 0, 0.4],
    "concluso": ["c5", 0.15, 0, 0.4, "e5", 0.15, 0, 0.4, "g5", 0.15, 0, 0.4, "c6", 0.15, 0, 0.4, "e6", 0.15, 0, 0.4, "g6", 0.4, 0, 0.4]
}

menu = {
    "n": "Nuova registrazione del valore",
    "c": "Cancella un valore",
    "f": "Modifica la data di fine progetto",
    "o": "Modifica l'obiettivo",
    "r": "Mostra il registro",
    "p": "Ascolta l'andamento dei valori (portamento)",
    "è": "Ascolta l'andamento dei valori (No portamento)",
    "+": "Ascolta l'andamento dei valori (scegli durata)",
    "b": "Vedi il progresso rispetto all'obiettivo",
    "t": "Vedi il progresso rispetto al tempo",
    "a": "Confronta tempo e obiettivo",
    "i": "Informazioni statistiche",
    "s": "Salva il registro",
    "m": "Mostra il menù",
    "q": "Elimina definitivamente tutti i dati",
    "e": "Esci dall'App"
}
menuchiavi = "".join([k + "." for k in menu.keys()])

def Salva(stato):
    try:
        stato_json = {
            "prjnome": stato["prjnome"],
            "prjdesc": stato["prjdesc"],
            "datainizio": stato["datainizio"].isoformat(),
            "datafine": stato["datafine"].isoformat(),
            "valori": {k.isoformat(): v for k, v in stato["valori"].items()},
            "obiettivo": stato["obiettivo"]
        }
        with open(RECORDNAME, "w", encoding="utf-8") as f:
            json.dump(stato_json, f, indent=4)
        Acusticator(SUONO["save"], kind=1, sync=False)
        print(f"\n{RECORDNAME} salvato.")
    except Exception as e:
        print(f"Errore durante il salvataggio: {e}")

def Carica():
    if os.path.exists(RECORDNAME):
        try:
            with open(RECORDNAME, "r", encoding="utf-8") as f:
                dati = json.load(f)
                
            stato = {
                "prjnome": dati["prjnome"],
                "prjdesc": dati["prjdesc"],
                "datainizio": dt.datetime.fromisoformat(dati["datainizio"]),
                "datafine": dt.datetime.fromisoformat(dati["datafine"]),
                "valori": {dt.datetime.fromisoformat(k): v for k, v in dati["valori"].items()},
                "obiettivo": dati["obiettivo"]
            }
            return stato
        except Exception as e:
            print(f"Errore durante il caricamento di {RECORDNAME}: {e}")
            return None
            
    if os.path.exists(OLD_RECORDNAME):
        try:
            with open(OLD_RECORDNAME, "rb") as f:
                dati = pickle.load(f)
                if not isinstance(dati, dict):
                    prjnome = dati
                    prjdesc = pickle.load(f)
                    datainizio = pickle.load(f)
                    datafine = pickle.load(f)
                    valori = pickle.load(f)
                    obiettivo = pickle.load(f)
                    stato = {
                        "prjnome": prjnome,
                        "prjdesc": prjdesc,
                        "datainizio": datainizio,
                        "datafine": datafine,
                        "valori": valori,
                        "obiettivo": obiettivo
                    }
                else:
                    stato = dati
            
            print(f"Trovato vecchio file {OLD_RECORDNAME}. Conversione in formato JSON in corso...")
            Salva(stato)
            try:
                os.rename(OLD_RECORDNAME, OLD_RECORDNAME + ".bak")
                print(f"Il vecchio file è stato rinominato in {OLD_RECORDNAME}.bak per sicurezza.")
            except Exception:
                pass
            return stato
        except Exception as e:
            print(f"Errore durante il caricamento di {OLD_RECORDNAME}: {e}")
            return None
            
    return None

def DigitaData():
    oggi = dt.datetime.now().replace(microsecond=0)
    anno = dgt(prompt=f"\nAnno? invio={oggi.year}> ", kind="i", imin=1970, imax=2500, default=oggi.year)
    mese = dgt(prompt=f"Mese? invio={oggi.month}> ", kind="i", imin=1, imax=12, default=oggi.month)
    
    # Calcolo esatto dei giorni per gestire anni bisestili e mesi
    if mese in [1, 3, 5, 7, 8, 10, 12]:
        maxgiorno = 31
    elif mese in [4, 6, 9, 11]:
        maxgiorno = 30
    else:
        # Anno bisestile
        if (anno % 4 == 0 and anno % 100 != 0) or (anno % 400 == 0):
            maxgiorno = 29
        else:
            maxgiorno = 28
            
    giorno = dgt(prompt=f"Giorno? invio={oggi.day}, max={maxgiorno}> ", kind="i", imin=1, imax=maxgiorno, default=oggi.day)
    ora = dgt(prompt=f"A che ora? invio={oggi.hour}> ", kind="i", imin=0, imax=23, default=oggi.hour)
    minuto = dgt(prompt=f"Minuti? invio={oggi.minute}> ", kind="i", imin=0, imax=59, default=oggi.minute)
    print("Grazie")
    return dt.datetime(year=anno, month=mese, day=giorno, hour=ora, minute=minuto)

def Inizializzazione():
    print(f"{RECORDNAME} non trovato o dati cancellati. Apertura nuova registrazione.")
    prjnome = dgt(prompt="Nome del progetto? ", kind="s", smin=5, smax=20).title()
    prjdesc = dgt(prompt="Descrizione del progetto? ", kind="s", smin=0, smax=1024)
    
    print("\nInserisci la data in cui inizia l'arco temporale.")
    datainizio = DigitaData()
    
    print("Molto bene, ora inserisci la data in cui prevedi di terminarlo.")
    while True:
        datafine = DigitaData()
        if datafine > datainizio:
            break
        print("La data di fine deve essere successiva a quella di inizio. Riprova.")
        
    valore = dgt(prompt="Inserisci il valore di partenza:> ", kind="f", fmin=0.0, fmax=1000.0)
    valori = {datainizio: valore}
    
    while True:
        obiettivo = dgt(prompt="Inserisci l'obiettivo da raggiungere:> ", kind="f", fmin=0.0, fmax=1000.0)
        if obiettivo != valore:
            break
        print("L'obiettivo non può essere uguale al valore di partenza. Riprova.")
        
    return {
        "prjnome": prjnome,
        "prjdesc": prjdesc,
        "datainizio": datainizio,
        "datafine": datafine,
        "valori": valori,
        "obiettivo": obiettivo
    }

def Reset(stato):
    attesa = dgt(prompt="ATTENZIONE! Sei sicuro di voler cancellare tutto?\nL'operazione è irreversibile! Digita 'sicuro'> ", kind="s", smin=0, smax=12, default="n")
    if attesa == "sicuro":
        Acusticator(SUONO["reset"], kind=1, sync=False)
        return Inizializzazione()
    print("Non tocco nulla.")
    return stato

def Humanize(d):
    giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    return f"{giorni[d.weekday()]} {d.day} {mesi[d.month - 1]} {d.year}, ore {d.hour:02d}:{d.minute:02d}"

def VPTempo(stato, show=False):
    datainizio = stato["datainizio"]
    datafine = stato["datafine"]
    durata = datafine - datainizio
    if show:
        print("\nProgressi sulla linea temporale del tuo progetto di controllo del valore.")
        print(f"Progetto iniziato in data {Humanize(datainizio)} terminerà il {Humanize(datafine)}, per un totale di {durata.days} giorni")
        
    oggi = dt.datetime.now().replace(microsecond=0)
    oggi1 = oggi.timestamp()
    d1 = datainizio.timestamp()
    d2 = datafine.timestamp()
    
    if d2 == d1:
        percentuale_tempo = 100.0
    else:
        percentuale_tempo = (oggi1 - d1) * 100 / (d2 - d1)
        
    if show:
        giorni_trascorsi = (oggi - datainizio).days
        if durata.days > 0:
            frazione = frac(giorni_trascorsi, durata.days)
        else:
            frazione = "1/1"
        print(f"Oggi è il {Humanize(oggi)}, giorno {giorni_trascorsi} di {durata.days}. Sei al {percentuale_tempo:+.2f}%, in frazione: {frazione}\ndel periodo di tempo impostato.")
    return percentuale_tempo

def VPObiettivo(stato, show=False):
    valori = stato["valori"]
    obiettivo = stato["obiettivo"]
    
    if show:
        print("\nProgressi ottenuti rispetto all'obiettivo prefissato:")
    
    if not valori:
        if show: print("Nessun valore registrato.")
        return 0.0
        
    valoreiniziale = valori[min(valori.keys())]
    valoreattuale = valori[max(valori.keys())]
    
    diff_obiettivo = obiettivo - valoreiniziale
    if diff_obiettivo == 0:
        percentuale_obiettivo = 100.0
    else:
        percentuale_obiettivo = (valoreattuale - valoreiniziale) * 100 / diff_obiettivo
        
    if show:
        print(f"Valore iniziale {valoreiniziale:+.2f}, attuale {valoreattuale:+.2f}, obiettivo {obiettivo:+.2f} = ({diff_obiettivo:+.2f}).")
        ottenuto = valoreattuale - valoreiniziale
        if diff_obiettivo != 0:
            frazione = frac(ottenuto / diff_obiettivo).limit_denominator()
        else:
            frazione = "1/1"
        print(f"Ottenuto {ottenuto:+.2f} pari al {percentuale_obiettivo:+.2f}%, in frazione: {frazione}")
        dafare = obiettivo - valoreattuale
        perc_dafare = dafare * 100 / diff_obiettivo if diff_obiettivo != 0 else 0.0
        print(f"Da fare {dafare:+.2f} pari al {perc_dafare:+.2f}%")
        
    return percentuale_obiettivo

def VRegistro(stato):
    valori = stato["valori"]
    print("\nDati presenti nel registro dei valori:")
    if not valori:
        print("Il registro è vuoto.")
        return
        
    contatore = 1
    differenza = 0.0
    for k in sorted(valori.keys()):
        v = valori[k]
        k1 = Humanize(k)
        if contatore == 1:
            print(f"({contatore}) - {v:+.2f}, (inizio) - di {k1}.")
        else:
            print(f"({contatore}) - {v:+.2f}, ({v-differenza:+.2f}) - di {k1}.")
        contatore += 1
        differenza = v
    print(f"Totale {len(valori)} records registrati.")

def Cancelladato(stato):
    valori = stato["valori"]
    if not valori:
        print("Il registro è vuoto.")
        return stato
        
    valore = dgt(prompt="\nInserisci il valore che vuoi cancellare:> ", kind="f", fmin=0.0, fmax=1000.0)
    ricerca = [k for k, v in valori.items() if v == valore]
    
    if not ricerca:
        print("Non è stato trovato il valore specificato all'interno del registro")
        return stato
    elif len(ricerca) == 1:
        chiave = ricerca[0]
        if chiave == min(valori.keys()):
            print("Impossibile eliminare il valore iniziale del progetto.")
            return stato
        print(f"Trovato il valore {valore}, registrato in data: {Humanize(chiave)}.")
        del valori[chiave]
        Acusticator(SUONO["delete"], kind=1, sync=False)
        print(f"Dato eliminato, ora il registro contiene {len(valori)} records")
        return stato
        
    print(f"Sono stati trovati {len(ricerca)} valori nel registro.\nDigita il numero di quello che vuoi eliminare.")
    multi = {}
    contatore = 1
    for j in ricerca:
        print(f"({contatore}) - in data - {Humanize(j)};")
        multi[contatore] = j
        contatore += 1
        
    scelta = dgt(prompt="Elemento da cancellare? (0 per annullare)> ", kind="i", imin=0, imax=len(multi))
    if scelta == 0:
        return stato
        
    chiave = multi[scelta]
    if chiave == min(valori.keys()):
        print("Impossibile eliminare il valore iniziale del progetto.")
        return stato
        
    del valori[chiave]
    Acusticator(SUONO["delete"], kind=1, sync=False)
    print(f"Dato eliminato. Ora il registro contiene {len(valori)} records.")
    return stato

def Nuovodato(stato):
    valori = stato["valori"]
    valore = dgt(prompt="\nInserisci il valore da registrare:> ", kind="f")
    Acusticator(SUONO["dato"], kind=1, sync=True)
    
    listavalori = list(valori.values())
    if listavalori:
        massimo = max(listavalori)
        minimo = min(listavalori)
        if valore > massimo:
            Acusticator(SUONO["sopra"], kind=1, sync=False)
            r = f"Nuovo record: {valore:+.2f} supera di {valore-massimo:+.2f} rispetto al massimo {massimo:+.2f}."
        elif valore < minimo:
            Acusticator(SUONO["sotto"], kind=1, sync=False)
            r = f"Nuovo record: {valore:+.2f} è inferiore di {minimo-valore:+.2f} rispetto al minimo {minimo:+.2f}."
        else:
            Acusticator(SUONO["mezzo"], kind=1, sync=False)
            r = f"Nuovo record nell'intervallo fra minimo {minimo:+.2f} < {valore-minimo:+.2f} < {valore:+.2f} < {massimo-valore:+.2f} < {massimo:+.2f}."
        print(r)
        
    adesso = dt.datetime.now().replace(microsecond=0)
    valori[adesso] = valore
    print(f"Fatto. Ora il registro contiene {len(valori)} records.")
    
    percentuale_obiettivo = VPObiettivo(stato)
    percentuale_tempo = VPTempo(stato)
    if percentuale_obiettivo >= 100 or percentuale_tempo >= 100:
        concluso = ConcludiProgetto(stato)
        return stato, concluso
        
    return stato, False

def VMenu():
    print(f"\nMenù di QUINQU, versione {VERSIONE}.")
    for k, v in menu.items():
        print(f"---( {k.upper()} ) - -> {v};")

def Cambiafine(stato):
    datafine_attuale = stato["datafine"]
    print(f"\nVecchia data di fine progetto: {Humanize(datafine_attuale)}.\nNuova data di fine progetto...")
    while True:
        nuova_data = DigitaData()
        if nuova_data > stato["datainizio"]:
            stato["datafine"] = nuova_data
            break
        print("La data di fine deve essere successiva a quella di inizio. Riprova.")
    return stato

def VConfronto(stato):
    valori = stato["valori"]
    datainizio = stato["datainizio"]
    datafine = stato["datafine"]
    obiettivo = stato["obiettivo"]
    
    if not valori:
        print("Dati insufficienti per un confronto.")
        return
        
    valoreiniziale = valori[min(valori.keys())]
    valoreattuale = valori[max(valori.keys())]
    
    diff_obiettivo = obiettivo - valoreiniziale
    op = (valoreattuale - valoreiniziale) * 100 / diff_obiettivo if diff_obiettivo != 0 else 100.0
    
    o = dt.datetime.now().replace(microsecond=0)
    o1 = o.timestamp()
    d1 = datainizio.timestamp()
    d2 = datafine.timestamp()
    
    ot = (o1 - d1) * 100 / (d2 - d1) if d2 != d1 else 100.0
    od = ot - op
    
    tolleranza = 10.0
    if abs(ot - op) <= tolleranza:
        oa = "progressione uniforme, molto bene!"
    elif ot < op - tolleranza:
        oa = "variazione del valore troppo rapida, rallentare."
    else:
        oa = "variazione del valore troppo lenta, accelerare."
        
    print(f"\nProgressi: tempo {ot:+.2f}% valore {op:+.2f}% (T={od:+.2f}%) {oa}")

def Infostatistiche(stato):
    valori = stato["valori"]
    obiettivo = stato["obiettivo"]
    if len(valori) < 4:
        print("Sono stati registrati pochi valori per mostrare le statistiche (minimo 4).")
        return
        
    print("\nInformazioni statistiche sui valori registrati.")
    l = list(valori.values())
    print("Numero di records:", len(l))
    
    piupiccolo = min(l)
    piugrande = max(l)
    listapiccoli = [k for k, v in valori.items() if v == piupiccolo]
    listagrandi = [k for k, v in valori.items() if v == piugrande]
    
    print(f"Il valore massimo è {piugrande:+.2f} e compare {len(listagrandi)} volte.")
    for j in listagrandi:
        print(f"\tData: {Humanize(j)};")
        
    print(f"Il valore minimo è {piupiccolo:+.2f} e compare {len(listapiccoli)} volte.")
    for j in listapiccoli:
        print(f"\tData: {Humanize(j)};")
        
    print(f"Media aritmetica dei valori: {statistics.fmean(l):+.2f}.")
    print(f"Mediane: bassa {statistics.median_low(l):+.2f}, media {statistics.median(l):+.2f}, alta {statistics.median_high(l):+.2f}.")
    print(f"Moda: {statistics.mode(l):+.2f}.")
    print(f"Deviazione standard: {statistics.stdev(l):+.2f}.")
    print(f"Varianza: {statistics.variance(l):+.2f}.")

    date_ordinate = sorted(valori.keys())
    primo_valore = valori[date_ordinate[0]]
    ultimo_valore = valori[date_ordinate[-1]]
    variazione_totale = ultimo_valore - primo_valore
    print(f"\nVariazione totale dal primo all'ultimo record: {variazione_totale:+.2f}")

    salti = []
    aumenti = 0
    cali = 0
    tempi_tra_inserimenti = []

    for i in range(1, len(date_ordinate)):
        data_prec = date_ordinate[i-1]
        data_corr = date_ordinate[i]
        val_prec = valori[data_prec]
        val_corr = valori[data_corr]
        delta_val = val_corr - val_prec
        delta_tempo = data_corr - data_prec
        
        salti.append((delta_val, data_corr))
        tempi_tra_inserimenti.append(delta_tempo.total_seconds())

        if delta_val > 0:
            aumenti += 1
        elif delta_val < 0:
            cali += 1

    salto_max = max(salti, key=lambda x: x[0])
    salto_min = min(salti, key=lambda x: x[0])

    print(f"Trend dei passaggi: {aumenti} aumenti, {cali} cali, {len(salti) - aumenti - cali} stabili.")
    if salto_max[0] > 0:
        print(f"Picco di aumento: {salto_max[0]:+.2f} registrato in data {Humanize(salto_max[1])}.")
    if salto_min[0] < 0:
        print(f"Picco di calo: {salto_min[0]:+.2f} registrato in data {Humanize(salto_min[1])}.")

    media_step = statistics.fmean([x[0] for x in salti])
    print(f"Variazione media per step: {media_step:+.2f}")

    media_tempo_sec = statistics.fmean(tempi_tra_inserimenti)
    giorni_media = media_tempo_sec // 86400
    ore_media = (media_tempo_sec % 86400) // 3600
    print(f"Frequenza media di inserimento: ogni {int(giorni_media)} giorni e {int(ore_media)} ore.")

    if variazione_totale != 0:
        tempo_trascorso = (date_ordinate[-1] - date_ordinate[0]).total_seconds()
        velocita = variazione_totale / tempo_trascorso if tempo_trascorso > 0 else 0
        da_fare = obiettivo - ultimo_valore
        
        if velocita != 0 and (da_fare / velocita) > 0:
            secondi_mancanti = da_fare / velocita
            data_stimata = date_ordinate[-1] + dt.timedelta(seconds=secondi_mancanti)
            print(f"Proiezione: mantenendo questa velocità, l'obiettivo ({obiettivo:+.2f}) potrebbe essere raggiunto il {Humanize(data_stimata)}.")
        else:
            print(f"Proiezione: andamento non in direzione dell'obiettivo ({obiettivo:+.2f}) o velocità nulla.")

def ConcludiProgetto(stato):
    prjnome = stato["prjnome"]
    prjdesc = stato["prjdesc"]
    datainizio = stato["datainizio"]
    datafine = stato["datafine"]
    valori = stato["valori"]
    obiettivo = stato["obiettivo"]
    
    print("\nIl progetto è concluso. Creazione del report finale...")
    Acusticator(SUONO["concluso"], kind=1, sync=False)
    
    if not valori:
        valoreiniziale = 0
        valoreattuale = 0
    else:
        valoreiniziale = valori[min(valori.keys())]
        valoreattuale = valori[max(valori.keys())]
        
    diff_obiettivo = obiettivo - valoreiniziale
    percentuale_obiettivo = (valoreattuale - valoreiniziale) * 100 / diff_obiettivo if diff_obiettivo != 0 else 100.0
    
    oggi = dt.datetime.now()
    diff_tempo = datafine.timestamp() - datainizio.timestamp()
    percentuale_tempo = (oggi.timestamp() - datainizio.timestamp()) * 100 / diff_tempo if diff_tempo != 0 else 100.0
    
    if percentuale_obiettivo >= 100:
        stato_progetto = f"Obiettivo raggiunto nel {percentuale_tempo:.2f}% del tempo a disposizione"
    elif percentuale_tempo >= 100:
        stato_progetto = f"Tempo scaduto: raggiunto il {percentuale_obiettivo:.2f}% dell'obiettivo"
    else:
        stato_progetto = f"Progetto in corso: raggiunto il {percentuale_obiettivo:.2f}% dell'obiettivo nel {percentuale_tempo:.2f}% del tempo"
        
    nome_file = f"Quinqu-{prjnome}.txt"
    try:
        with open(nome_file, "w", encoding="utf-8") as f:
            f.write(f"Nome del progetto: {prjnome}\n")
            f.write(f"Descrizione: {prjdesc}\n")
            f.write(f"Data inizio: {Humanize(datainizio)}\n")
            f.write(f"Data fine: {Humanize(datafine)}\n")
            f.write(f"Valore iniziale: {valoreiniziale:+.2f}\n")
            f.write(f"Valore obiettivo: {obiettivo:+.2f}\n")
            f.write(f"{stato_progetto}\n\n")
            f.write("Registro dei valori:\n")
            contatore = 1
            differenza = 0.0
            for k in sorted(valori.keys()):
                v = valori[k]
                k1 = Humanize(k)
                if contatore == 1:
                    f.write(f"({contatore}) - {v:+.2f}, (inizio) - di {k1}.\n")
                else:
                    f.write(f"({contatore}) - {v:+.2f}, ({v-differenza:+.2f}) - di {k1}.\n")
                contatore += 1
                differenza = v
                
            from io import StringIO
            buf = StringIO()
            original_stdout = sys.stdout
            try:
                sys.stdout = buf
                Infostatistiche(stato)
                sys.stdout = original_stdout
                f.write(buf.getvalue())
            finally:
                buf.close()
                sys.stdout = original_stdout
                
            f.write(f"\nReport prodotto il {Humanize(dt.datetime.now())}\n")
            f.write(f"Applicazione: Quanto In Quanto (Quinqu) versione {VERSIONE}\n")
        print(f"Report salvato come {nome_file}.")
    except Exception as e:
        print(f"Errore durante la creazione del report: {e}")
        
    if os.path.exists(RECORDNAME):
        try:
            os.remove(RECORDNAME)
            print(f"{RECORDNAME} cancellato.")
        except OSError as e:
            print(f"Impossibile cancellare {RECORDNAME}: {e}")
            
    print("Applicazione chiusa in quanto il progetto è terminato.")
    return True

def main():
    Acusticator(SUONO["startup"], kind=1, sync=False)
    print(f"Welcome a {AUTORE}!\nApplicazione: Quanto In Quanto (Quinqu)\nVersione {VERSIONE}\nUn'App per tenere traccia dei progressi in un obiettivo,\nesprimibile con un valore numerico, da raggiungere in un determinato arco temporale.")
    print("Controllo la presenza di una registrazione salvata...")
    
    stato = Carica()
    if stato:
        print(f"Registro caricato correttamente. Contiene {len(stato['valori'])} records.")
        percentuale_obiettivo = VPObiettivo(stato)
        percentuale_tempo = VPTempo(stato)
        if percentuale_obiettivo >= 100 or percentuale_tempo >= 100:
            if ConcludiProgetto(stato):
                return
    else:
        stato = Inizializzazione()
        Salva(stato)
        print("Iniziamo")

    print("Digita M per leggere il menù dell'App")
    while True:
        attesa = key(prompt=f"CMD: {menuchiavi}> ").lower()
        if attesa == "m":
            VMenu()
        elif attesa == "e":
            Acusticator(SUONO["shutdown"], kind=1, sync=True)
            Salva(stato)
            break
        elif attesa == "n":
            stato, concluso = Nuovodato(stato)
            if concluso:
                return
        elif attesa == "c":
            stato = Cancelladato(stato)
        elif attesa == "r":
            VRegistro(stato)
        elif attesa == "p":
            if len(stato["valori"]) > 0:
                dati = [stato["valori"][k] for k in sorted(stato["valori"].keys())]
                durata = len(dati) * 0.25
                print(f"\nRiproduzione dell'andamento di {len(dati)} valori registrati (durata: {durata:.1f}s)...")
                sonify(dati, duration=durata, ptm=True, vol=0.5)
            else:
                print("\nNessun valore registrato per la riproduzione.")
        elif attesa == "è":
            if len(stato["valori"]) > 0:
                dati = [stato["valori"][k] for k in sorted(stato["valori"].keys())]
                durata = len(dati) * 0.25
                print(f"\nRiproduzione dell'andamento di {len(dati)} valori registrati (durata: {durata:.1f}s)...")
                sonify(dati, duration=durata, ptm=False, vol=0.5)
            else:
                print("\nNessun valore registrato per la riproduzione.")
        elif attesa == "+":
            if len(stato["valori"]) > 0:
                dati = [stato["valori"][k] for k in sorted(stato["valori"].keys())]
                durata = dgt("Durata? ", kind="f", fmin=3.0, fmax=60.0, default=len(dati) * 0.25)
                print(f"\nRiproduzione dell'andamento di {len(dati)} valori registrati (durata: {durata:.1f}s)...")
                sonify(dati, duration=durata, ptm=True, vol=0.5)
            else:
                print("\nNessun valore registrato per la riproduzione.")
        elif attesa == "b":
            VPObiettivo(stato, show=True)
        elif attesa == "i":
            Infostatistiche(stato)
        elif attesa == "a":
            VConfronto(stato)
        elif attesa == "f":
            stato = Cambiafine(stato)
        elif attesa == "q":
            stato = Reset(stato)
        elif attesa == "t":
            VPTempo(stato, show=True)
        elif attesa == "o":
            nuovo_ob = dgt(prompt=f"Obiettivo attuale: {stato['obiettivo']}, nuovo? >", kind="f", fmin=0.0, fmax=1000.0)
            if nuovo_ob != stato['valori'][min(stato['valori'].keys())]:
                stato['obiettivo'] = nuovo_ob
                print("Nuovo obiettivo impostato.")
            else:
                print("L'obiettivo non può coincidere con il valore iniziale.")
        elif attesa == "s":
            Salva(stato)
        else:
            print(f"\n{attesa} non è un comando valido.")
            VMenu()

    print("Arrivederci!")

if __name__ == "__main__":
    main()
