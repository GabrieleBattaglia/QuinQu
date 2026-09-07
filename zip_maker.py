# Quinqu, utilita': prepara l'archivio per la distribuzione.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5, modalita' auto).

"""Comprime il risultato di PyInstaller in un solo archivio.

Tutto il mestiere sta in GBUtils, cosi' la regola sulle esclusioni e' una
sola per tutti i progetti. Qui restano soltanto i nomi di Quinqu.

Quinqu si compila in un file unico, quindi dentro dist c'e' soltanto
l'eseguibile: la collezione dei suoni, dichiarata nei datas dello spec,
viaggia dentro di lui e non va cercata accanto. Per questo la cartella da
comprimere e' dist e non dist/quinqu.

Si lasciano fuori l'archivio degli obiettivi, la sua copia di sicurezza e
i report dei progetti conclusi: nascono tutti provando l'eseguibile prima
di comprimere, e conterrebbero i dati veri di chi ha compilato.
"""

import sys

from GBUtils import crea_archivio_release

FUORI = [
    "quinqu.json",
    "quinqu.json.bak",
    "quinqu.db",
    "quinqu.db.bak",
    "Quinqu-*.txt",
]


def main():
    try:
        crea_archivio_release("quinqu", cartella_dist="dist", escludi=FUORI)
    except (FileNotFoundError, OSError) as e:
        print(f"Archivio non creato: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
