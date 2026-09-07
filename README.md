# QuinQu

Quanto in Quanto. Un simpatico tool che traccia la progressione di un valore numerico in un determinato lasso temporale.

Si dichiara un valore di partenza, un obiettivo da raggiungere e la data entro cui raggiungerlo. Poi, di volta in volta, si registra il valore del momento, con un commento facoltativo. Quinqu dice a che punto si è rispetto all'obiettivo, a che punto si è rispetto al tempo, quale sarebbe il valore giusto per arrivare in orario, quanto si è distanti dalla prossima tappa e quando si arriverà al traguardo se si continua di questo passo. Sa anche far ascoltare l'andamento dei valori come una melodia, e produce un report finale quando il progetto si chiude.

Può seguire fino a dieci obiettivi diversi, ciascuno con la sua storia.

## Accessibilità

Quinqu è pensato per essere usato con uno screen reader. L'output si legge in modo lineare, non ci sono separatori grafici né tabelle allineate a colonne, e le righe informative sono spezzate in blocchi di circa quaranta caratteri per la lettura sul display braille.

## Installazione da sorgente

Serve Python 3.10 o successivo.

Le dipendenze si installano con:

    pip install -r requirements.txt

Manca però una dipendenza che pip non può scaricare, perché non sta su PyPI: è GBUtils, la libreria condivisa del parco software di IZ4APU. Va clonata a parte:

    git clone https://github.com/GabrieleBattaglia/GBUtils.git

poi si mette la sua cartella in PYTHONPATH, oppure si copiano `GBUtils.py` e `Acu_Collection.json` accanto a `quinqu.py`. Senza `Acu_Collection.json` il programma funziona ma resta muto.

## Dati

Gli obiettivi si salvano in `quinqu.json`, accanto al programma, con una copia di sicurezza in `quinqu.json.bak`. Un eventuale `quinqu.db` di una versione vecchia viene convertito automaticamente al primo avvio.
