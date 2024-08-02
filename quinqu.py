# Quanto in Quanto (Quinqu). Data di concepimento 10/02/2024.
# Programma per seguire e salvare i progressi nel raggiungimento di un obiettivo il cui valore possa essere espresso in numeri
# Precedentemente: dieta 1.6.4
# Nuovo nome by Ginny & Manu & me
# 28 giugno 2024, spostato su GitHub

#Qimport
from GBUtils import dgt, key
import datetime as dt
import pickle, fractions, statistics

#QConstants
VERSIONE="2.0.2 del 1 agosto 2024"
RECORDNAME="quinqu.db"

#QVariables
menu={"N":"Nuova registrazione del valore",
						"C":"Cancella un valore",
						"F":"Modifica la data di fine progetto",
						"O":"Modifica l'obiettivo",
						"R":"Mostra il registro",
						"B":"Vedi il progresso rispetto all'obiettivo",
						"T":"Vedi il progresso rispetto al tempo",
						"A":"Confronta tempo e obiettivo",
						"I":"Informazioni statistiche",
						"S":"Salva il registro",
						"M":"Mostra il menù",
						"Q":"Elimina definitivamente tutti i dati",
						"E":"Esci dall'App"}
menuchiavi=''
for k in menu.keys():
	menuchiavi+=str(k).lower()+"."

#QFunctions
def Reset(prjnome,prjdesc,valori,datainizio,datafine,obiettivo):
	'''Inizializza tutti i dati'''
	attesa=dgt(prompt="ATTENZIONE! Sei sicuro di voler cancellare tutto?\n\tL'operazione è irreversibile! Digita 'sicuro'> ",kind="s",smin=0,smax=12,default="n")
	if attesa == "sicuro":
		prjnome,prjdesc,valori,datainizio,datafine,obiettivo=Inizializzazione()
	else: print("Non tocco nulla.")
	return prjnome,prjdesc,valori,datainizio,datafine,obiettivo
def Infostatistiche(valori):
	if len(valori)<4:
		print("Sono stati registrati pochi valori per mostrare le statistiche.")
		return
	print("\nInformazioni statistiche sui valori registrati.")
	l=list(valori.values())
	print("Numero di records:",len(l))
	piupiccolo=min(l); piugrande=max(l)
	listapiccoli, listagrandi = [], []
	for k, v in valori.items():
		if v==piugrande: listagrandi.append(k)
		if v==piupiccolo: listapiccoli.append(k)
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
	return

def Humanize(d):
	'''Normalizza la data per una visualizzazione più comoda'''
	return f"{d.day}/{d.month}/{d.year} {d.hour}:{d.minute}"

def VPTempo(valori,datainizio,datafine,obiettivo, show=False):
	'''Visualizza progressi sulla linea temporale'''
	if show: print("\nProgressi sulla linea temporale del tuo progetto di controllo del valore.")
	durata=datafine-datainizio
	if show: print(f"Progetto iniziato in data {Humanize(datainizio)} terminerà il {Humanize(datafine)}, per un totale di {durata.days} giorni")
	oggi=dt.datetime.now().replace(microsecond=0)
	oggi1=oggi.timestamp(); d1=datainizio.timestamp(); d2=datafine.timestamp()
	percentuale_tempo=(oggi1-d1)*100/(d2-d1)
	if show: print(f"Oggi è il {Humanize(oggi)}, giorno {(oggi-datainizio).days} di {durata.days}. Sei al {percentuale_tempo:+.2f}%, in frazione: {fractions.Fraction((oggi-datainizio).days, durata.days)}\n\tdel periodo di tempo impostato.")
	return percentuale_tempo

def VPObiettivo(valori, datainizio,datafine,obiettivo, show=False):
	'''Progressi rispetto all'obiettivo'''
	if show: print("\nProgressi ottenuti rispetto all'obiettivo prefissato:")
	valoreiniziale=valori[datainizio]
	valoreattuale=valori[list(valori.keys())[-1]]
	percentuale_obiettivo=(valoreattuale-valoreiniziale)*100/(obiettivo-valoreiniziale)
	if show: print(f"Valore iniziale {valoreiniziale:+.2f}, attuale {valoreattuale:+.2f}, obiettivo {obiettivo:+.2f} = ({obiettivo-valoreiniziale:+.2f}).")
	if show: print(f"Ottenuto {valoreattuale-valoreiniziale:+.2f} pari al {percentuale_obiettivo:+.2f}%, in frazione: {fractions.Fraction(int(valoreattuale-valoreiniziale), int(obiettivo-valoreiniziale))}")
	if show: print(f"Da fare {obiettivo-valoreattuale:+.2f} pari al {(obiettivo-valoreattuale)*100/(obiettivo-valoreiniziale):+.2f}%")
	return percentuale_obiettivo

def VRegistro(p):
	'''Visualizza il db'''
	print("\nDati presenti nel registro dei valori:")
	contatore=1; differenza=0.0
	for k,v in p.items():
		k1=Humanize(k)
		print(f"({contatore}) - {v:+.2f}, ({v-differenza:+.2f}) - del {k1}.")
		contatore+=1
		differenza=v
	print(f"Totale {len(p)} records registrati.")
	return

def Cancelladato(p):
	'''cancella un record da valori'''
	valore=dgt(prompt="\nInserisci il valore che vuoi cancellare:> ", kind="f", fmin=0.0, fmax=1000.0)
	ricerca=[]
	for k,v in valori.items():
		if valore==v: ricerca.append(k)
	if len(ricerca)==0:
		print("Non è stato trovato il valore specificato all'interno del registro")
		return p
	elif len(ricerca)==1:
		print(f"Trovato il valore {valore}, registrato in data: {Humanize(ricerca[0])}.")
		del p[ricerca[0]]
		print(f"Dato eliminato, ora il registro contiene {len(p)} records")
		return p
	print(f"Sono stati trovati {len(ricerca)} nel registro.\nDigita il numero di quello che vuoi eliminare.")
	multi={}
	contatore=1
	for j in ricerca:
		print(f"({contatore}) - in data - {str(j)};")
		multi[contatore]=j
		contatore+=1
	scelta=dgt(prompt="Elemento da cancellare?> ",kind="i", imin=1,imax=len(multi))
	del p[multi[scelta]]
	print(f"Dato eliminato. Ora il registro contiene {len(p)} records.")
	return p

def Nuovodato(p):
	'''aggiunge un record a valori'''
	valore=dgt(prompt="\nInserisci il valore da registrare:> ", kind="f", fmin=0.0, fmax=1000.0)
	listavalori=list(p.values())
	if valore>max(listavalori): r=f"Nuovo record: {valore:+.2f} supera di {valore-max(listavalori):+.2f} rispetto al massimo {max(listavalori):+.2f}."
	elif valore<min(listavalori): r=f"Nuovo record: {valore:+.2f} è inferiore di {valore-min(listavalori):+.2f} rispetto al minimo {min(listavalori):+.2f}."
	else: r=f"Nuovo record nell'intervallo fra minimo {min(listavalori):+.2f} < {valore-min(listavalori):+.2f} < {valore:+.2f} > {valore-max(listavalori):+.2f} > {max(listavalori):+.2f}."
	print(r)
	adesso=dt.datetime.now().replace(microsecond=0)
	p[adesso]=valore
	print(f"Fatto. Ora il registro contiene {len(p)} records.")
	percentuale_obiettivo = VPObiettivo(p, datainizio, datafine, obiettivo)
	percentuale_tempo = VPTempo(p, datainizio, datafine, obiettivo)
	if percentuale_obiettivo >= 100 or percentuale_tempo >= 100:
		ConcludiProgetto()
	return p

def VMenu():
	'''Mostra il menù dell'app'''
	print(f"\nMenù di QUINQU, versione {VERSIONE}.")
	for k, v in menu.items():
		print(f"---( {k} ) - -> {v};")
	return

def Salva():
	f=open(RECORDNAME,"wb")
	pickle.dump(prjnome, f, pickle.HIGHEST_PROTOCOL)
	pickle.dump(prjdesc, f, pickle.HIGHEST_PROTOCOL)
	pickle.dump(datainizio, f, pickle.HIGHEST_PROTOCOL)
	pickle.dump(datafine, f, pickle.HIGHEST_PROTOCOL)
	pickle.dump(valori, f, pickle.HIGHEST_PROTOCOL)
	pickle.dump(obiettivo, f, pickle.HIGHEST_PROTOCOL)
	f.close()
	print(f"\n{RECORDNAME} salvato.")
	return

def DigitaData():
	'''Restituisce 5 valori con cui settare un oggetto datetime.date()'''
	oggi=dt.datetime.now().replace(microsecond=0)
	anno=dgt(prompt=f"\nAnno? invio={oggi.year}> ",kind="i",imin=1970,imax=2500, default=oggi.year)
	mese=dgt(prompt=f"Mese? invio={oggi.month}> ",kind="i",imin=1,imax=12, default=oggi.month)
	if mese in [1,3,5,7,8,10,12]: maxgiorno=31
	elif mese in [4,6,9,11]: maxgiorno=30
	else: maxgiorno=29
	giorno=dgt(prompt=f"Giorno? invio={oggi.day}, max={maxgiorno}> ",kind="i",imin=1,imax=maxgiorno, default=oggi.day)
	ora=dgt(prompt=f"A che ora? invio={oggi.hour}> ",kind="i",imin=0,imax=23, default=oggi.hour)
	minuto=dgt(prompt=f"Minuti? invio={oggi.minute}> ",kind="i",imin=0,imax=59, default=oggi.minute)
	print("Grazie")
	return minuto, ora, giorno,mese,anno

def Inizializzazione():
	'''Inizializza e restituisce i 6 dati fondamentali'''
	print(f"{RECORDNAME} non trovato. Apertura nuova registrazione.")
	prjnome=dgt(prompt="Nome del progetto? ",kind="s", smin=5,smax=20).title()
	prjdesc=dgt(prompt="Descrizione del progetto? ",kind="s", smin=0,smax=1024)
	print("\nInserisci la data in cui inizia l'arco temporale.")
	minuto, ora, giorno, mese, anno = DigitaData()
	datainizio=dt.datetime(minute=minuto, hour=ora, day=giorno, month=mese, year=anno)
	print("Molto bene, ora inserisci la data in cui prevedi di terminarlo.")
	minuto, ora, giorno, mese, anno = DigitaData()
	datafine=dt.datetime(minute=minuto, hour=ora, day=giorno, month=mese, year=anno)
	valori={}
	valore=dgt(prompt="Inserisci il valore di partenza:> ", kind="f", fmin=0.0, fmax=1000.0)
	valori[datainizio]=valore
	obiettivo=dgt(prompt="Inserisci l'obiettivo da raggiungere:> ", kind="f", fmin=0.0, fmax=1000.0)
	return prjnome,prjdesc,valori,datainizio,datafine,obiettivo

def Cambiafine(datafine):
	'''Cambia la data di fine progetto'''
	print(f"\nVecchia data di fine progetto: {Humanize(datafine)}.\nNuova data di fine progetto...")
	minuto, ora, giorno, mese, anno = DigitaData()
	datafine=dt.datetime(minute=minuto, hour=ora, day=giorno, month=mese, anno=anno)
	return datafine

def VConfronto(valori,datainizio,datafine,obiettivo):
	'''Mostra le percentuali di progresso'''
	valoreiniziale=valori[datainizio]
	valoreattuale=valori[list(valori.keys())[-1]]
	op=(valoreattuale-valoreiniziale)*100/(obiettivo-valoreiniziale)
	o=dt.datetime.now().replace(microsecond=0)
	o1=o.timestamp(); d1=datainizio.timestamp(); d2=datafine.timestamp()
	ot=(o1-d1)*100/(d2-d1)
	od=ot-op
	if ot>op-10.0 and ot<op+10.0: oa="progressione uniforme, molto bene!"
	elif ot<op-10.0: oa="variazione del valore troppo rapida, rallentare"
	elif ot>op+10.0: oa="variazione del valore troppo lenta, accelerare"
	print(f"\nProgressi: tempo {ot:+.2f}% valore {op:+.2f}% ({od:+.2f}% {oa}")
	return

def ConcludiProgetto():
	'''Dichiara il progetto concluso e salva il report finale'''
	print("\nIl progetto è concluso. Creazione del report finale...")
	# Calcolo delle percentuali di tempo e obiettivo raggiunto
	valoreiniziale = valori[datainizio]
	valoreattuale = valori[list(valori.keys())[-1]]
	percentuale_obiettivo = (valoreattuale-valoreiniziale) * 100 / (obiettivo-valoreiniziale)
	oggi = dt.datetime.now()
	percentuale_tempo = (oggi.timestamp() - datainizio.timestamp()) * 100 / (datafine.timestamp() - datainizio.timestamp())
	
	# Determinazione dello stato del progetto
	if valoreattuale >= obiettivo:
		stato_progetto = f"Obbiettivo raggiunto nel {percentuale_tempo:.2f}% del tempo a disposizione"
	else:
		percentuale_mancante = 100 - percentuale_obiettivo
		stato_progetto = f"Obbiettivo mancato: {percentuale_mancante:.2f}% al raggiungimento dell'obbiettivo"
	with open(f"Quinqu-{prjnome}.txt", "w", encoding="utf-8") as f:
		f.write(f"Nome del progetto: {prjnome}\n")
		f.write(f"Descrizione: {prjdesc}\n")
		f.write(f"Data inizio: {Humanize(datainizio)}\n")
		f.write(f"Data fine: {Humanize(datafine)}\n")
		f.write(f"Valore iniziale: {valoreiniziale:+.2f}\n")
		f.write(f"Valore obiettivo: {obiettivo:+.2f}\n")
		f.write(f"{stato_progetto}\n\n")
		f.write("Registro dei valori:\n")
		contatore=1; differenza=0.0
		for k,v in valori.items():
			k1=Humanize(k)
			f.write(f"({contatore}) - {v:+.2f}, ({v-differenza:+.2f}) - del {k1}.\n")
			contatore+=1
			differenza=v
		from io import StringIO
		buf = StringIO()
		import sys
		original_stdout = sys.stdout
		try:
			sys.stdout = buf
			Infostatistiche(valori)
			sys.stdout = original_stdout
			f.write(buf.getvalue())  # Aggiunge il contenuto di buf al file
		finally:
			buf.close()
			sys.stdout = original_stdout
		f.write(f"\nReport prodotto il {Humanize(dt.datetime.now())}\n")
		f.write(f"Applicazione: Quanto In Quanto (Quinqu) versione {VERSIONE}\n")
	print(f"Report salvato come Quinqu-{prjnome}.txt.")
	import os
	if os.path.exists(RECORDNAME):
		os.remove(RECORDNAME)
		print("Quinqu.db cancellato. Applicazione chiusa.")
	else: print("Problema nell'individuazione del DB")
	exit()

#QMain
print(f"Benvenuto in Quanto In Quanto (Quinqu), versione {VERSIONE}.\nUn'App per tenere traccia dei progressi in un obiettivo,\nesprimibile con un valore numerico, da raggiungere in un determinato arco temporale.")
print("Controllo la presenza di una registrazione salvata...")
try:
	f=open(RECORDNAME,"rb")
	prjnome=pickle.load(f)
	prjdesc=pickle.load(f)
	datainizio=pickle.load(f)
	datafine=pickle.load(f)
	valori=pickle.load(f)
	obiettivo=pickle.load(f)
	f.close()
	print(f"Registro caricato correttamente. Contiene {len(valori)} records.")
	percentuale_obiettivo = VPObiettivo(valori, datainizio, datafine, obiettivo)
	percentuale_tempo = VPTempo(valori, datainizio, datafine, obiettivo)
	if percentuale_obiettivo >= 100 or percentuale_tempo >= 100:
		ConcludiProgetto()
except IOError:
	prjnome,prjdesc,valori,datainizio,datafine,obiettivo=Inizializzazione()
	Salva()
	print("Iniziamo")

#QMainLoop
print("Digita M per leggere il menù dell'App")
while True:
	attesa=key(prompt=f"CMD: {str(menuchiavi)}> ").lower()
	if attesa=="m": VMenu()
	elif attesa=="e": break
	elif attesa=="n": valori=Nuovodato(valori)
	elif attesa=="c": valori=Cancelladato(valori)
	elif attesa=="r": VRegistro(valori)
	elif attesa=="b": VPObiettivo(valori,datainizio,datafine,obiettivo,show=True)
	elif attesa=="i": Infostatistiche(valori)
	elif attesa=="a": VConfronto(valori,datainizio,datafine,obiettivo)
	elif attesa=="f": datafine=Cambiafine(datafine)
	elif attesa=="q": prjnome,prjdesc,valori,datainizio,datafine,obiettivo=Reset(valori,datainizio,datafine,obiettivo)
	elif attesa=="t": VPTempo(valori,datainizio,datafine,obiettivo,show=True)
	elif attesa=="o":
		obiettivo=dgt(prompt=f"Obiettivo attuale: {obiettivo}, nuovo? >",kind="f",fmin=0.0,fmax=1000.0)
		print("Nuovo obiettivo impostato.")
	elif attesa=="s": Salva()
	else:
		print(attesa, "Non è un comando valido.")
		VMenu()
attesa=dgt(prompt="Vuoi salvare? (S|N)> ",kind="s",smin=1,smax=1,default="s")
if attesa in "sS":
	Salva()
print("Arrivederci!")
