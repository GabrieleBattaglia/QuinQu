# Quanto in Quanto (Quinqu). Data di concepimento 10/02/2024.
# Programma per seguire e salvare i progressi nel raggiungimento di un obiettivo il cui valore possa essere espresso in numeri

import os
import sys
import json
import pickle
import statistics
import datetime as dt
import numpy as np
from fractions import Fraction as frac
from GBUtils import dgt, Acusticator, sonify, menu

VERSIONE = "4.3.1 del 19 luglio 2026"
AUTORE = "Gabriele"
RECORDNAME = "quinqu.json"
OLD_RECORDNAME = "quinqu.db"

SUONO_FALLBACK = {
    "quinqu_startup": ["c5", 0.08, 0.0, 0.4, "e5", 0.08, 0.0, 0.4, "g5", 0.08, 0.0, 0.4, "c6", 0.25, 0.0, 0.4],
    "quinqu_shutdown": ["c6", 0.08, 0.0, 0.4, "g5", 0.08, 0.0, 0.4, "e5", 0.08, 0.0, 0.4, "c5", 0.25, 0.0, 0.4],
    "salita_ideale": ["c4.g4", 0.3, 0.0, 0.4],
    "discesa_ideale": ["g4.c4", 0.3, 0.0, 0.4],
    "in_linea_ideale": ["e5", 0.15, 0.0, 0.4, "p", 0.05, 0.0, 0.4, "e5", 0.15, 0.0, 0.4],
    "convalida0": ["c4", 0.1, 0.0, 0.4, "f6", 0.1, 0.0, 0.4, "d#5", 0.1, 0.0, 0.4, "g#6", 0.4, 0.0, 0.4],
    "vittoria": ["f#4", 0.16, 0.0, 0.3, "c#5", 0.16, 0.0, 0.3, "e4", 0.16, 0.0, 0.3, "b5", 0.28, 0.0, 0.3],
    "cancellato": ["b2.g#2", 0.22, 0.0, 0.4, "p", 0.06, 0.0, 0.4, "a2", 0.08, 0.0, 0.4],
    "written_ok": ["c4", 0.04, 0.0, 0.4, "c4.b4", 0.04, 0.0, 0.4],
    "rifiuto": ["g3.f3", 0.5, 0.0, 0.4, "p", 0.04, 0.0, 0.4, "g7", 0.02, 0.0, 0.4],
    "rifiutato": ["g3.d3", 0.18, 0.0, 0.4, "f3.c3", 0.18, 0.0, 0.4, "d#3.a#2", 0.18, 0.0, 0.4],
    "campanellino": ["c8.c#8", 0.5, 0.0, 0.4],
    "mostra": ["f2", 0.2, 0.0, 0.4, "g#2", 0.2, 0.0, 0.4, "d2", 0.2, 0.0, 0.4],
    "lista": ["d4.a6", 0.1, 0.0, 0.4],
    "controllo_ok": ["d4", 0.05, 0.0, 0.4, "f6", 0.05, 0.0, 0.4]
}

def RiproduciEffetto(nome_preset, base_vol=0.4, sync=True):
    try:
        import GBUtils
        db_path = os.path.join(os.path.dirname(os.path.abspath(GBUtils.__file__)), "Acu_Collection.json")
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
            if nome_preset in db:
                preset = db[nome_preset]
                score_flat = []
                for q in preset['score']:
                    note, dur, pan, vol_delta = q
                    vol = max(0.0, min(1.0, base_vol + vol_delta))
                    score_flat.extend([note, dur, pan, vol])
                Acusticator(score_flat, kind=preset['kind'], adsr=preset['adsr'], sync=sync)
                return
    except Exception:
        pass
    if nome_preset in SUONO_FALLBACK:
        Acusticator(SUONO_FALLBACK[nome_preset], kind=1, sync=sync)

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
    "statistiche": "Informazioni statistiche",
    "salva": "Salva il registro",
    "cambia": "Cambia obiettivo gestito",
    "elimina": "Elimina l'obiettivo corrente",
    "menu": "Mostra il menù",
    "reset": "Elimina definitivamente tutti i dati (RESET GLOBALE)",
    "esci": "Esci dall'App"
}

def Salva(progetti):
    try:
        progetti_json = {}
        for pid, p in progetti.items():
            progetti_json[pid] = {
                "prjnome": p["prjnome"],
                "prjdesc": p["prjdesc"],
                "datainizio": p["datainizio"].isoformat(),
                "datafine": p["datafine"].isoformat(),
                "valori": {k.isoformat(): v for k, v in p["valori"].items()},
                "obiettivo": p["obiettivo"]
            }
        with open(RECORDNAME, "w", encoding="utf-8") as f:
            json.dump(progetti_json, f, indent=4)
        RiproduciEffetto("written_ok")
        print(f"\n{RECORDNAME} salvato.")
    except Exception as e:
        print(f"Errore durante il salvataggio: {e}")

def Carica():
    if os.path.exists(RECORDNAME):
        try:
            with open(RECORDNAME, "r", encoding="utf-8") as f:
                dati = json.load(f)
                
            if "prjnome" in dati:
                dati = {"0": dati}

            progetti = {}
            for pid, p in dati.items():
                progetti[pid] = {
                    "prjnome": p["prjnome"],
                    "prjdesc": p["prjdesc"],
                    "datainizio": dt.datetime.fromisoformat(p["datainizio"]),
                    "datafine": dt.datetime.fromisoformat(p["datafine"]),
                    "valori": {dt.datetime.fromisoformat(k): v for k, v in p["valori"].items()},
                    "obiettivo": p["obiettivo"]
                }
            return progetti
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
            progetti = {"0": stato}
            Salva(progetti)
            try:
                os.rename(OLD_RECORDNAME, OLD_RECORDNAME + ".bak")
                print(f"Il vecchio file è stato rinominato in {OLD_RECORDNAME}.bak per sicurezza.")
            except Exception:
                pass
            return progetti
        except Exception as e:
            print(f"Errore durante il caricamento di {OLD_RECORDNAME}: {e}")
            return None
            
    return None

def DigitaData():
    oggi = dt.datetime.now().replace(microsecond=0)
    anno = dgt(prompt=f"\nAnno? invio={oggi.year}> ", kind="i", imin=1970, imax=2500, default=oggi.year)
    mese = dgt(prompt=f"Mese? invio={oggi.month}> ", kind="i", imin=1, imax=12, default=oggi.month)
    
    if mese in [1, 3, 5, 7, 8, 10, 12]:
        maxgiorno = 31
    elif mese in [4, 6, 9, 11]:
        maxgiorno = 30
    else:
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

def Reset(progetti):
    attesa = dgt(prompt="ATTENZIONE! Sei sicuro di voler cancellare TUTTI i progetti?\nL'operazione è irreversibile! Digita 'sicuro'> ", kind="s", smin=0, smax=12, default="n")
    if attesa == "sicuro":
        RiproduciEffetto("rifiutato")
        RiproduciEffetto("cancellato")
        return {"0": Inizializzazione()}, "0"
    print("Non tocco nulla.")
    return progetti, None

def Humanize(d):
    giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    return f"{giorni[d.weekday()]} {d.day} {mesi[d.month - 1]} {d.year}, ore {d.hour:02d}:{d.minute:02d}"

def StampaTabellino(vi, vc, vi_id, ob):
    v_sorted = sorted([vi, vc, vi_id, ob])
    s = "Tabellino di marcia: "
    for i in range(len(v_sorted)):
        s += f"{v_sorted[i]:+.2f}"
        if i < len(v_sorted) - 1:
            diff = v_sorted[i+1] - v_sorted[i]
            s += f" < {diff:+.2f} < "
    print(s)

def VPTempo(stato, show=False):
    datainizio = stato["datainizio"]
    datafine = stato["datafine"]
    durata = datafine - datainizio
    if show:
        RiproduciEffetto("mostra")
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
        RiproduciEffetto("mostra")
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

def CalcolaProiezione(valori, obiettivo, n_punti=None):
    date_ordinate = sorted(valori.keys())
    if len(date_ordinate) < 2:
        return None, None
    if n_punti is not None:
        date_ordinate = date_ordinate[-n_punti:]
        if len(date_ordinate) < 2:
            return None, None
    x = [d.timestamp() for d in date_ordinate]
    y = [valori[d] for d in date_ordinate]
    try:
        slope, _ = np.polyfit(x, y, 1)
    except Exception:
        return None, None
    if slope == 0:
        return None, 0.0
    ultimo_valore = y[-1]
    da_fare = obiettivo - ultimo_valore
    velocita_giornaliera = slope * 86400
    secondi_mancanti = da_fare / slope
    if secondi_mancanti > 0:
        data_stimata = date_ordinate[-1] + dt.timedelta(seconds=secondi_mancanti)
        return data_stimata, velocita_giornaliera
    else:
        return None, velocita_giornaliera

def VRegistro(stato):
    valori = stato["valori"]
    print("\nDati presenti nel registro dei valori:")
    if not valori:
        RiproduciEffetto("rifiuto")
        print("Il registro è vuoto.")
        return
        
    RiproduciEffetto("lista")
        
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
        RiproduciEffetto("rifiuto")
        print("Il registro è vuoto.")
        return stato
        
    valore = dgt(prompt="Inserisci il valore che vuoi cancellare:> ", kind="f", fmin=0.0, fmax=1000.0)
    ricerca = [k for k, v in valori.items() if v == valore]
    
    if not ricerca:
        RiproduciEffetto("rifiuto")
        print("Non è stato trovato il valore specificato all'interno del registro")
        return stato
    elif len(ricerca) == 1:
        chiave = ricerca[0]
        if chiave == min(valori.keys()):
            RiproduciEffetto("rifiuto")
            print("Impossibile eliminare il valore iniziale del progetto.")
            return stato
        print(f"Trovato il valore {valore}, registrato in data: {Humanize(chiave)}.")
        del valori[chiave]
        RiproduciEffetto("cancellato")
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
        RiproduciEffetto("campanellino")
        return stato
        
    chiave = multi[scelta]
    if chiave == min(valori.keys()):
        RiproduciEffetto("rifiuto")
        print("Impossibile eliminare il valore iniziale del progetto.")
        return stato
        
    del valori[chiave]
    RiproduciEffetto("cancellato")
    print(f"Dato eliminato. Ora il registro contiene {len(valori)} records.")
    return stato

def Nuovodato(stato):
    valori = stato["valori"]
    valore = dgt(prompt="Inserisci il valore da registrare:> ", kind="f")
    RiproduciEffetto("convalida0")
    
    listavalori = list(valori.values())
    if listavalori:
        massimo = max(listavalori)
        minimo = min(listavalori)
        if valore > massimo:
            RiproduciEffetto("vittoria", base_vol=0.2)
            r = f"Nuovo record: {valore:+.2f} supera di {valore-massimo:+.2f} rispetto al massimo {massimo:+.2f}."
        elif valore < minimo:
            RiproduciEffetto("rifiutato")
            r = f"Nuovo record: {valore:+.2f} è inferiore di {minimo-valore:+.2f} rispetto al minimo {minimo:+.2f}."
        else:
            RiproduciEffetto("controllo_ok")
            r = f"Nuovo record nell'intervallo fra minimo {minimo:+.2f} < {valore-minimo:+.2f} < {valore:+.2f} < {massimo-valore:+.2f} < {massimo:+.2f}."
        print(r)
        
    adesso = dt.datetime.now().replace(microsecond=0)
    valori[adesso] = valore
    print(f"Fatto. Ora il registro contiene {len(valori)} records.")
    
    valoreiniziale = valori[min(valori.keys())]
    obiettivo = stato["obiettivo"]
    durata_totale = (stato["datafine"] - stato["datainizio"]).total_seconds()
    tempo_trascorso = (adesso - stato["datainizio"]).total_seconds()
    
    if durata_totale > 0:
        perc_t = tempo_trascorso / durata_totale
        valore_ideale = valoreiniziale + (obiettivo - valoreiniziale) * perc_t
    else:
        valore_ideale = obiettivo
        
    diff_ideale = valore - valore_ideale
    if abs(valore_ideale) > 0:
        perc_diff_ideale = (diff_ideale / abs(valore_ideale)) * 100
    else:
        diff_obiettivo = obiettivo - valoreiniziale
        perc_diff_ideale = (diff_ideale / abs(diff_obiettivo)) * 100 if diff_obiettivo != 0 else 0.0

    if abs(diff_ideale) < 0.01:
        giudizio = "perfettamente in linea"
        RiproduciEffetto("in_linea_ideale")
    elif diff_ideale < 0:
        giudizio = "inferiore"
        RiproduciEffetto("discesa_ideale")
    else:
        giudizio = "superiore"
        RiproduciEffetto("salita_ideale")

    print(f"Valore ideale utile per completare in tempo: {valore_ideale:.2f}.")
    if abs(diff_ideale) >= 0.01:
        print(f"Il valore inserito è {giudizio} a quello utile di {abs(diff_ideale):.2f} (deviazione {perc_diff_ideale:+.2f}%).")
    else:
        print("Il valore inserito è esattamente in pari con la tabella di marcia ideale.")
        
    StampaTabellino(valoreiniziale, valore, valore_ideale, obiettivo)
    
    data_stimata_glob, vel_glob = CalcolaProiezione(valori, obiettivo)
    data_stimata_rec, vel_rec = CalcolaProiezione(valori, obiettivo, n_punti=5)
    if data_stimata_glob:
        print(f"Proiezione Storica (Globale):\n  Traguardo: {Humanize(data_stimata_glob)} (velocità: {vel_glob:+.2f}/giorno)")
    else:
        if vel_glob is not None:
            print(f"Proiezione Storica (Globale):\n  Andamento non in direzione dell'obiettivo (velocità: {vel_glob:+.2f}/giorno)")
        else:
            print("Proiezione Storica (Globale):\n  Dati insufficienti (minimo 2 valori)")
    if data_stimata_rec:
        print(f"Proiezione Recente (ultimi 5 dati):\n  Traguardo: {Humanize(data_stimata_rec)} (velocità: {vel_rec:+.2f}/giorno)")
    else:
        if vel_rec is not None:
            print(f"Proiezione Recente (ultimi 5 dati):\n  Andamento non in direzione dell'obiettivo (velocità: {vel_rec:+.2f}/giorno)")
        else:
            print("Proiezione Recente (ultimi 5 dati):\n  Dati insufficienti (minimo 2 valori)")
            
    percentuale_obiettivo = VPObiettivo(stato)
    percentuale_tempo = VPTempo(stato)
    if percentuale_obiettivo >= 100 or percentuale_tempo >= 100:
        concluso = ConcludiProgetto(stato)
        return stato, concluso
        
    return stato, False

def VMenu():
    print(f"\nMenù di QUINQU, versione {VERSIONE}.")
    menu(d=main_menu, show_only=True)

def SelezionaProgetto(progetti):
    opzioni = {}
    for pid, p in progetti.items():
        perc_ob = VPObiettivo(p, show=False)
        perc_t = VPTempo(p, show=False)
        desc = f"{p['prjnome']} ({len(p['valori'])} dati) [Obiettivo: {perc_ob:.1f}%, Tempo: {perc_t:.1f}%]\n    > {p['prjdesc']}"
        opzioni[pid] = desc
        
    if len(progetti) < 10:
        opzioni["n"] = "-- Crea Nuovo Obiettivo --"
                
    RiproduciEffetto("lista")
    print("\nObiettivi disponibili:")
    while True:
        scelta = menu(d=opzioni, p="Scegli obiettivo: ", show=True, keyslist=True)
        if scelta is None:
            if progetti:
                print("Selezione annullata.")
                return list(progetti.keys())[0]
            else:
                continue
                
        if scelta == "n":
            for i in range(10):
                if str(i) not in progetti:
                    nuovo_id = str(i)
                    break
            progetti[nuovo_id] = Inizializzazione()
            return nuovo_id
            
        return scelta

def Cambiafine(stato):
    datafine_attuale = stato["datafine"]
    print(f"\nVecchia data di fine progetto: {Humanize(datafine_attuale)}.\nNuova data di fine progetto...")
    while True:
        nuova_data = DigitaData()
        if nuova_data > stato["datainizio"]:
            stato["datafine"] = nuova_data
            RiproduciEffetto("roger_cw_conferma")
            break
        RiproduciEffetto("rifiuto")
        print("La data di fine deve essere successiva a quella di inizio. Riprova.")
    return stato

def VConfronto(stato):
    valori = stato["valori"]
    datainizio = stato["datainizio"]
    datafine = stato["datafine"]
    obiettivo = stato["obiettivo"]
    
    if not valori:
        RiproduciEffetto("rifiuto")
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
        RiproduciEffetto("controllo_ok")
    elif ot < op - tolleranza:
        oa = "variazione del valore troppo rapida, rallentare."
        RiproduciEffetto("campanellino")
    else:
        oa = "variazione del valore troppo lenta, accelerare."
        RiproduciEffetto("rifiutato")
        
    print(f"\nProgressi: tempo {ot:+.2f}% valore {op:+.2f}% (T={od:+.2f}%) {oa}")

def Infostatistiche(stato):
    valori = stato["valori"]
    obiettivo = stato["obiettivo"]
    if len(valori) < 4:
        RiproduciEffetto("rifiuto")
        print("Sono stati registrati pochi valori per mostrare le statistiche (minimo 4).")
        return
        
    RiproduciEffetto("mostra")
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
    dati_ordinati = sorted(valori.items(), key=lambda x: x[1])
    indices = np.array_split(range(len(dati_ordinati)), 4)
    print("\nSuddivisione in quartili per valore:")
    for idx, idx_group in enumerate(indices, 1):
        chunk = [dati_ordinati[i] for i in idx_group]
        chunk_vals = [item[1] for item in chunk]
        chunk_dates = [item[0] for item in chunk]
        date_min = min(chunk_dates)
        date_max = max(chunk_dates)
        c_min = float(np.min(chunk_vals))
        c_mean = float(np.mean(chunk_vals))
        c_max = float(np.max(chunk_vals))
        print(f"\tQ{idx}: {Humanize(date_min)} - {Humanize(date_max)}")
        print(f"\tmin: {c_min:+.2f}, med: {c_mean:+.2f}, max: {c_max:+.2f}")

    dati_cronologici = sorted(valori.items(), key=lambda x: x[0])
    indices_c = np.array_split(range(len(dati_cronologici)), 4)
    print("\nSuddivisione in quartili per tempo:")
    for idx, idx_group in enumerate(indices_c, 1):
        chunk = [dati_cronologici[i] for i in idx_group]
        chunk_vals = [item[1] for item in chunk]
        chunk_dates = [item[0] for item in chunk]
        date_min = min(chunk_dates)
        date_max = max(chunk_dates)
        c_min = float(np.min(chunk_vals))
        c_mean = float(np.mean(chunk_vals))
        c_max = float(np.max(chunk_vals))
        print(f"\tQ{idx} (Tempo): {Humanize(date_min)} - {Humanize(date_max)}")
        print(f"\tmin: {c_min:+.2f}, med: {c_mean:+.2f}, max: {c_max:+.2f}")

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

    if salti:
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

    data_stimata_glob, vel_glob = CalcolaProiezione(valori, obiettivo)
    data_stimata_rec, vel_rec = CalcolaProiezione(valori, obiettivo, n_punti=5)
    if data_stimata_glob:
        print(f"Proiezione Storica (Globale):\n  Traguardo: {Humanize(data_stimata_glob)} (velocità: {vel_glob:+.2f}/giorno)")
    else:
        if vel_glob is not None:
            print(f"Proiezione Storica (Globale):\n  Andamento non in direzione dell'obiettivo (velocità: {vel_glob:+.2f}/giorno)")
        else:
            print("Proiezione Storica (Globale):\n  Dati insufficienti (minimo 2 valori)")
    if data_stimata_rec:
        print(f"Proiezione Recente (ultimi 5 dati):\n  Traguardo: {Humanize(data_stimata_rec)} (velocità: {vel_rec:+.2f}/giorno)")
    else:
        if vel_rec is not None:
            print(f"Proiezione Recente (ultimi 5 dati):\n  Andamento non in direzione dell'obiettivo (velocità: {vel_rec:+.2f}/giorno)")
        else:
            print("Proiezione Recente (ultimi 5 dati):\n  Dati insufficienti (minimo 2 valori)")

    oggi = dt.datetime.now().replace(microsecond=0)
    giorni_rimanenti = (stato["datafine"] - oggi).total_seconds() / 86400
    da_fare_oggi = obiettivo - ultimo_valore
    if giorni_rimanenti > 0 and da_fare_oggi != 0:
        valore_giornaliero = da_fare_oggi / giorni_rimanenti
        print(f"Tabella di marcia: occorre acquisire {valore_giornaliero:+.2f} al giorno per completare in tempo.")
    elif giorni_rimanenti <= 0 and da_fare_oggi != 0:
        print("Tempo a disposizione scaduto per calcolare il progresso giornaliero necessario.")

def ConcludiProgetto(stato):
    prjnome = stato["prjnome"]
    prjdesc = stato["prjdesc"]
    datainizio = stato["datainizio"]
    datafine = stato["datafine"]
    valori = stato["valori"]
    obiettivo = stato["obiettivo"]
    
    print("\nIl progetto è concluso. Creazione del report finale...")
    RiproduciEffetto("vittoria")
    
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
            
    print(f"Progetto '{prjnome}' terminato e report generato.")
    return True

def main():
    RiproduciEffetto("quinqu_startup")
    print(f"Welcome a {AUTORE}!\nApplicazione: Quanto In Quanto (Quinqu)\nVersione {VERSIONE}\nUn'App per tenere traccia dei progressi in un obiettivo,\nesprimibile con un valore numerico, da raggiungere in un determinato arco temporale.")
    print("Controllo la presenza di una registrazione salvata...")
    
    progetti = Carica()
    if progetti is None:
        progetti = {}
        
    if not progetti:
        RiproduciEffetto("campanellino")
        print("Nessun obiettivo presente. Creiamone uno.")
        nuovo_stato = Inizializzazione()
        progetti["0"] = nuovo_stato
        id_corrente = "0"
        Salva(progetti)
    else:
        RiproduciEffetto("controllo_ok")
        if len(progetti) == 1:
            id_corrente = list(progetti.keys())[0]
            print(f"Unico obiettivo trovato e caricato: {progetti[id_corrente]['prjnome']}")
        else:
            id_corrente = SelezionaProgetto(progetti)
            Salva(progetti)

    stato = progetti[id_corrente]

    percentuale_obiettivo = VPObiettivo(stato)
    percentuale_tempo = VPTempo(stato)
    if percentuale_obiettivo >= 100 or percentuale_tempo >= 100:
        if ConcludiProgetto(stato):
            prj_concluso = stato["prjnome"]
            del progetti[id_corrente]
            Salva(progetti)
            if len(progetti) == 0:
                print("Tutti gli obiettivi sono stati conclusi.")
                attesa_nuovo = dgt(prompt="\nVuoi creare un nuovo obiettivo? (S|N)> ", kind="s", smin=1, smax=1, default="s").lower()
                if attesa_nuovo == "s":
                    nuovo_stato = Inizializzazione()
                    progetti["0"] = nuovo_stato
                    id_corrente = "0"
                    stato = progetti[id_corrente]
                    Salva(progetti)
                else:
                    return
            elif len(progetti) == 1:
                id_corrente = list(progetti.keys())[0]
                stato = progetti[id_corrente]
                print(f"\nObiettivo '{prj_concluso}' concluso. Rimane un solo obiettivo attivo: '{stato['prjnome']}', che viene caricato automaticamente.")
            else:
                print(f"\nObiettivo '{prj_concluso}' concluso.")
                id_corrente = SelezionaProgetto(progetti)
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
            break
        elif attesa == "nuovo":
            stato, concluso = Nuovodato(stato)
            if concluso:
                prj_concluso = stato["prjnome"]
                del progetti[id_corrente]
                Salva(progetti)
                if len(progetti) == 0:
                    print("Tutti gli obiettivi sono stati conclusi.")
                    attesa_nuovo = dgt(prompt="Vuoi creare un nuovo obiettivo? (S|N)> ", kind="s", smin=1, smax=1, default="s").lower()
                    if attesa_nuovo == "s":
                        nuovo_stato = Inizializzazione()
                        progetti["0"] = nuovo_stato
                        id_corrente = "0"
                        stato = progetti[id_corrente]
                        Salva(progetti)
                    else:
                        break
                elif len(progetti) == 1:
                    id_corrente = list(progetti.keys())[0]
                    stato = progetti[id_corrente]
                    print(f"\nObiettivo '{prj_concluso}' concluso. Rimane un solo obiettivo attivo: '{stato['prjnome']}', che viene caricato automaticamente.")
                else:
                    print(f"\nObiettivo '{prj_concluso}' concluso.")
                    id_corrente = SelezionaProgetto(progetti)
                    stato = progetti[id_corrente]
        elif attesa == "cancella":
            stato = Cancelladato(stato)
        elif attesa == "registro":
            VRegistro(stato)
        elif attesa == "suono_p":
            if len(stato["valori"]) > 0:
                dati = [stato["valori"][k] for k in sorted(stato["valori"].keys())]
                durata = len(dati) * 0.25
                print(f"\nRiproduzione dell'andamento di {len(dati)} valori registrati (durata: {durata:.1f}s)...")
                sonify(dati, duration=durata, ptm=True, vol=0.3)
            else:
                RiproduciEffetto("rifiuto")
                print("\nNessun valore registrato per la riproduzione.")
        elif attesa == "suono_np":
            if len(stato["valori"]) > 0:
                dati = [stato["valori"][k] for k in sorted(stato["valori"].keys())]
                durata = len(dati) * 0.25
                print(f"\nRiproduzione dell'andamento di {len(dati)} valori registrati (durata: {durata:.1f}s)...")
                sonify(dati, duration=durata, ptm=False, vol=0.3)
            else:
                RiproduciEffetto("rifiuto")
                print("\nNessun valore registrato per la riproduzione.")
        elif attesa == "suono_d":
            if len(stato["valori"]) > 0:
                dati = [stato["valori"][k] for k in sorted(stato["valori"].keys())]
                durata = dgt(prompt="Durata? ", kind="f", fmin=3.0, fmax=60.0, default=len(dati) * 0.25)
                print(f"\nRiproduzione dell'andamento di {len(dati)} valori registrati (durata: {durata:.1f}s)...")
                sonify(dati, duration=durata, ptm=True, vol=0.3)
            else:
                RiproduciEffetto("rifiuto")
                print("\nNessun valore registrato per la riproduzione.")
        elif attesa == "progresso_ob":
            VPObiettivo(stato, show=True)
        elif attesa == "statistiche":
            Infostatistiche(stato)
        elif attesa == "confronto":
            VConfronto(stato)
        elif attesa == "fine":
            stato = Cambiafine(stato)
        elif attesa == "reset":
            progetti, nuovo_id = Reset(progetti)
            if nuovo_id is not None:
                id_corrente = nuovo_id
                stato = progetti[id_corrente]
                Salva(progetti)
        elif attesa == "progresso_t":
            VPTempo(stato, show=True)
        elif attesa == "obiettivo":
            nuovo_ob = dgt(prompt=f"Obiettivo attuale: {stato['obiettivo']}, nuovo? >", kind="f", fmin=0.0, fmax=1000.0)
            if nuovo_ob != stato['valori'][min(stato['valori'].keys())]:
                stato['obiettivo'] = nuovo_ob
                RiproduciEffetto("roger_cw_conferma")
                print("Nuovo obiettivo impostato.")
            else:
                RiproduciEffetto("rifiuto")
                print("L'obiettivo non può coincidere con il valore iniziale.")
        elif attesa == "salva":
            Salva(progetti)
        elif attesa == "cambia":
            id_corrente = SelezionaProgetto(progetti)
            stato = progetti[id_corrente]
            RiproduciEffetto("campanellino")
            print(f"Passato a {stato['prjnome']}.")
        elif attesa == "apri":
            if len(progetti) >= 10:
                RiproduciEffetto("rifiuto")
                print("Numero massimo di obiettivi raggiunto (massimo 10).")
            else:
                for i in range(10):
                    if str(i) not in progetti:
                        nuovo_id = str(i)
                        break
                progetti[nuovo_id] = Inizializzazione()
                id_corrente = nuovo_id
                stato = progetti[id_corrente]
                Salva(progetti)
                print(f"Creato e caricato il nuovo obiettivo: {stato['prjnome']}")
        elif attesa == "elimina":
            attesa_del = dgt(prompt=f"Vuoi davvero eliminare l'obiettivo {stato['prjnome']}? (sicuro)> ", kind="s", smin=0, smax=12, default="n")
            if attesa_del == "sicuro":
                RiproduciEffetto("cancellato")
                prj_eliminato = stato["prjnome"]
                del progetti[id_corrente]
                if len(progetti) == 0:
                    print("Tutti gli obiettivi sono stati eliminati.")
                    nuovo_stato = Inizializzazione()
                    progetti["0"] = nuovo_stato
                    id_corrente = "0"
                    stato = progetti[id_corrente]
                    Salva(progetti)
                    print(f"Obiettivo eliminato. Passato a {stato['prjnome']}.")
                elif len(progetti) == 1:
                    id_corrente = list(progetti.keys())[0]
                    stato = progetti[id_corrente]
                    Salva(progetti)
                    print(f"Obiettivo '{prj_eliminato}' eliminato. Passato all'unico rimasto: {stato['prjnome']}.")
                else:
                    id_corrente = SelezionaProgetto(progetti)
                    stato = progetti[id_corrente]
                    Salva(progetti)
                    print(f"Obiettivo '{prj_eliminato}' eliminato. Passato a {stato['prjnome']}.")
            else:
                RiproduciEffetto("campanellino")
                print("Operazione annullata.")
        else:
            RiproduciEffetto("rifiuto")
            print(f"\n{attesa} non è un comando valido.")
            VMenu()

if __name__ == "__main__":
    main()