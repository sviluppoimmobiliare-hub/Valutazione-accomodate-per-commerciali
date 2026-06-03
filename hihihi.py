import time
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import google.generativeai as gen

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file("credenziali.json", scopes=SCOPES)
gc = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)
id_foglio = "1zt0wUA_f5oCl-VqoA3mMJ7vjeRthcpE7IEPRbiXSgbs"
fogli_di_valutazione = gc.open_by_key(id_foglio)

api_gemini = "AQ.Ab8RN6JljaEYxNc6rNT-WFeO-WWG5VI0V1GB2rZBMCXDOW5Qiw"
gen.configure(api_key=api_gemini)


# ESTRATTORE OPZIONI
def estrattore_opzioni(coordinata, etichetta, nome_foglio):
    url_api = f"https://sheets.googleapis.com/v4/spreadsheets/{fogli_di_valutazione.id}"
    parametri = {
        'ranges': f'{nome_foglio}!{coordinata}',
        'includeGridData': True
    }
    risposta_grezza = gc.http_client.request("GET", url_api, params=parametri)
    risposta = risposta_grezza.json()

    try:
        risposta_server = risposta['sheets'][0]['data'][0]['rowData'][0]['values'][0]['dataValidation']['condition'][
            'values']
        lista_opzioni = [v['userEnteredValue'] for v in risposta_server]
        scelta = st.selectbox(f"Seleziona {etichetta}", options=lista_opzioni)
        risultato_finale = scelta

    except KeyError:
        risposta_server = risposta['sheets'][0]['data'][0]['rowData'][0]['values'][0]['dataValidation']['condition'][
            'type']
        if risposta_server == 'BOOLEAN':
            lista_opzioni = ["Si", "No"]
            scelta = st.selectbox(f"Seleziona {etichetta}", options=lista_opzioni)
            if scelta == "Si":
                risultato_finale = True
            else:
                risultato_finale = False
    return risultato_finale


# IMPOSTAZIONE INIZIALE
st.set_page_config(page_title="Valutazione Accomodate Homa")
st.header("Modello di Valutazione Preliminare Accomodate")

Inserimento_dati = fogli_di_valutazione.get_worksheet(0)
area = {
    "Nord": ["valle d'aosta", "piemonte", "liguria", "lombardia", "trentino-alto adige", "veneto",
             "friuli-venezia giulia", "emilia-romagna"],
    "Centro": ["toscana", "umbria", "marche", "lazio"]
}


with st.form("form_valutazione"):
    # GENERALITA'
    st.markdown("**GENERALITA'**")
    col1, col2, col3 = st.columns(3)
    with col1:
        link_annuncio = st.text_input("Link Annuncio")
    with col2:
        stato_attuale = st.text_input("Stato attuale dell'appartamento")
    with col3:
        durata_contrattuale = int(
            st.number_input("Durata di contratto, se non disponibile lasciare il campo vuoto ", value=0))

    # SPECIFICHE GEOGRAFICHE
    st.markdown("**SPECIFICHE GEOGRAFICHE**")
    col1, col2, col3 = st.columns(3)
    with col1:
        Indirizzo = st.text_input("Indirizzo")
    with col2:
        citta = estrattore_opzioni("B5", "Città", Inserimento_dati.title)
    with col3:
        Regione = st.text_input("Regione").lower()

    # SPECIFICHE FISICHE
    st.markdown("**SPECIFICHE FISICHE**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metri_quadri = st.number_input("Metri Quadri")
    with col2:
        camere_singole = int(st.number_input("Camere Singole"))
    with col3:
        camere_doppie = int(st.number_input("Camere Doppie"))
    with col4:
        camere_triple = int(st.number_input("Camere Triple"))

    st.markdown("**Locali Secondari**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        bagni = st.number_input("Bagni", value=0)
    with col2:
        cucina = st.number_input("Cucina", value=0)
    with col3:
        soggiorno = st.number_input("Soggiorno", value=0)
    with col4:
        altri_locali = st.text_input("Altri locali?")

    # IMPIANTISTICA
    st.markdown("**Impiantistica**")
    col1, col2, col3 = st.columns(3)
    with col1:
        tipologia_riscaldamento = estrattore_opzioni("B6", "Tipologia Riscaldamento", "Inserimento dati")
        riscaldamento_compreso_oneri = estrattore_opzioni("B19", "Riscaldamento compreso negli oneri?",
                                                          "Inserimento dati")
    with col2:
        alimentazione_acqua = estrattore_opzioni("B7", "Acqua calda, come viene alimentata", "Inserimento dati")
        acqua_compresa_oneri = estrattore_opzioni("B18", "Acqua compresa negli oneri?", "Inserimento dati")
    with col3:
        raffrescamento = estrattore_opzioni("B8", "Raffrescamento", "Inserimento dati")
        piano_cottura = estrattore_opzioni("B9", "Piano cottura", "Inserimento dati")

    # SPECIFICHE GESTIONALI ESTERNE
    st.markdown("**SPECIFICHE GESTIIONALI ESTERNE**")
    col1, col2 = st.columns(2)
    with col1:
        società_di_locazione = estrattore_opzioni("B22",
                                                  "Società di Locazione (Homa no cedolare, oppure Rent Hub cedolare al 21% ma solo studenti)",
                                                  "Inserimento dati")
        agenzia = estrattore_opzioni("B24", "Agenzia", "Inserimento dati")
        mensilità_deposito = st.number_input("Mensilità di deposito cauzionale")
        mesi_sfitto = st.number_input("Mesi di sfitto iniziale?")
    with col2:
        canone_mensile = st.number_input("Canone mensile richiesto? Se non disponibile inserire 0")
        fee_agenzia = st.number_input("Fee di Agenzia?")
        inizio_locazione = st.date_input("Inizio mese di locazione(se disponibile)")
        oneri_condominiali = st.number_input("Oneri Condominiali mensili")


    # SPECIFICHE GESTIONALI INTERNE
    st.markdown("**SPECIFICHE GESTIIONALI INTERNE**")
    canoni_di_locazione = st.number_input("Canoni di locazione attiva")
    coordinate_camere = ["B13", "B16", "B19", "B22", "B25", "B28", "B31", "B34", "B37", "B40", "B43", "B46", "B49"]

    pricing1, pricing2, pricing3 = {}, {}, {}
    pricing_unico_singole, pricing_unico_doppie, pricing_unico_triple = 0.0, 0.0, 0.0

    # Calcolo coordinate prezzi singole
    coordinate_prezzising = []
    valore_iniziale = 13
    for i in range(0, int(camere_singole)):
        coordinate_prezzising.append(f"D{valore_iniziale}")
        valore_iniziale += 3

    pricing_singole = st.checkbox("Camere singole a prezzi diversi?")
    if pricing_singole:
        for i in range(0, int(camere_singole)):
            pricing1[f"camera {i}"] = st.number_input(f"Prezzo camera singola {i + 1}", key=f"input_singola_{i}")
    else:
        pricing_unico_singole = st.number_input("Prezzo singole unico per tutte le camere?")

    # Calcolo coordinate prezzi doppie
    coordinate_prezzidopp = []
    for i in range(0, int(camere_doppie)):
        coordinate_prezzidopp.append(f"D{valore_iniziale}")
        valore_iniziale += 3

    pricing_doppie = st.checkbox("Camere doppie a prezzi diversi?")
    if pricing_doppie:
        for i in range(0, int(camere_doppie)):
            pricing2[f"camera {i}"] = st.number_input(f"Prezzo camera doppia {i + 1}", key=f"input_doppia_{i}")
    else:
        pricing_unico_doppie = st.number_input("Prezzo doppie unico per tutte le camere?")

    # Calcolo coordinate prezzi triple
    coordinate_prezzitriple = []
    for i in range(0, int(camere_triple)):
        coordinate_prezzitriple.append(f"D{valore_iniziale}")
        valore_iniziale += 3

    pricing_triple = st.checkbox("Camere triple a prezzi diversi?")
    if pricing_triple:
        for i in range(0, int(camere_triple)):
            pricing3[f"camera {i + 1}"] = st.number_input(f"Prezzo camera tripla {i + 1}", key=f"input_tripla_{i}")
    else:
        pricing_unico_triple = st.number_input("Prezzo triple unico per tutte le camere?")

    # ARREDAMENTO
    st.markdown("**ARREDAMENTO**")
    arredamento_bagni = st.checkbox("I bagni vanno arredati?")
    coordinate_bagni = {
        1: ["B14", "B15", "B16", "B17"],
        2: ["B22", "B23", "B24", "B25"],
        3: ["B30", "B31", "B32", "B33"]
    }
    arredamento_cam = st.checkbox("Le camere vanno arredate?")
    coordinate_camere_arredo = {
        "singole": ["B47", "B48", "B49", "B50", "B51", "B52", "B53", "B54", "B55", "B56", "B57", "B58"],
        "doppie": ["B63", "B64", "B65", "B66", "B67", "B68", "B69", "B70", "B71", "B72", "B73", "B74"],
        "triple": ["B79", "B80", "B81", "B82", "B83", "B84", "B85", "B86", "B87", "B88", "B89", "B90"]
    }
    arredamento_cuc = st.checkbox("La cucina va arredata?")
    arredamento_sog = st.checkbox("Il soggiorno va arredato?")
    coordinate_sog_cuc = {
        "cucina": ["B5", "B6", "B7", "B8", "B9"],
        "soggiorno": ["B38", "B39", "B40", "B41", "B42"]
    }

    st.markdown(
        """Salva i dati inseriti, tali dati verranno pre-compilati nel modello di valutazione interna, **cliccare l'opzione solo se sono i dati definitivi per cui si ha bisogno di procedere**""")
    note = st.text_input("Eventuali note su come svolgere la valutazione")

    # PULSANTE DI INVIO DEL FORM (INVIA TUTTI I DATI INSIEME)
    salva_dati = st.form_submit_button("Salva i dati")


if salva_dati:
    with st.spinner("Salvataggio in corso"):
        fogli_di_valutazione.update_title(Indirizzo)


        camere_totali = camere_singole + camere_doppie + camere_triple
        batch_ws0 = [
            {'range': 'B31', 'values': [[durata_contrattuale]]},
            {'range': 'D3', 'values': [[link_annuncio]]},
            {'range': 'B17', 'values': [[oneri_condominiali]]},
            {'range': 'D1', 'values': [[note]]},
            {'range': 'D2', 'values': [[stato_attuale]]},
            {'range': 'B5', 'values': [[citta]]},
            {'range': 'B2', 'values': [[Indirizzo]]},
            {'range': 'B4', 'values': [[metri_quadri]]},
            {'range': 'E15', 'values': [[camere_triple]]},
            {'range': 'G14', 'values': [[camere_doppie]]},
            {'range': 'E14', 'values': [[camere_singole]]},
            {'range': 'B14', 'values': [[camere_totali]]},
            {'range': 'B13', 'values': [[bagni]]},
            {'range': 'B11', 'values': [[cucina]]},
            {'range': 'B12', 'values': [[soggiorno]]},
            {'range': 'B15', 'values': [[altri_locali]]},
            {'range': 'B6', 'values': [[tipologia_riscaldamento]]},
            {'range': 'B19', 'values': [[riscaldamento_compreso_oneri]]},
            {'range': 'B7', 'values': [[alimentazione_acqua]]},
            {'range': 'B18', 'values': [[acqua_compresa_oneri]]},
            {'range': 'B8', 'values': [[raffrescamento]]},
            {'range': 'B9', 'values': [[piano_cottura]]},
            {'range': 'B22', 'values': [[società_di_locazione]]},
            {'range': 'B24', 'values': [[agenzia]]},
            {'range': 'B25', 'values': [[fee_agenzia]]},
            {'range': 'B26', 'values': [[mensilità_deposito]]},
            {'range': 'B23', 'values': [[canone_mensile]]},
            {'range': 'B32', 'values': [[mesi_sfitto]]},
            {'range': 'B29', 'values': [[str(inizio_locazione)]]}
        ]
        Inserimento_dati.batch_update(batch_ws0)


        punti_regione = 20 if Regione in area["Nord"] else (13 if Regione in area["Centro"] else 6)
        fogli_di_valutazione.get_worksheet(5).update_acell("C5", punti_regione)


        batch_ws4 = []
        tipo_cella = (["Singola"] * camere_singole + ["Doppia"] * camere_doppie + ["Tripla"] * camere_triple)
        for i, tipo in enumerate(tipo_cella):
            if i >= len(coordinate_camere):
                break
            batch_ws4.append({'range': coordinate_camere[i], 'values': [[tipo]]})

        for i in range(0, int(camere_singole)):
            val = pricing1[f"camera {i}"] if pricing_singole else pricing_unico_singole
            batch_ws4.append({'range': coordinate_prezzising[i], 'values': [[val]]})

        for i in range(0, int(camere_doppie)):
            val = pricing2[f"camera {i}"] if pricing_doppie else pricing_unico_doppie
            batch_ws4.append({'range': coordinate_prezzidopp[i], 'values': [[val]]})

        for i in range(0, int(camere_triple)):
            val = pricing3[f"camera {i + 1}"] if pricing_triple else pricing_unico_triple
            batch_ws4.append({'range': coordinate_prezzitriple[i], 'values': [[val]]})

        if batch_ws4:
            fogli_di_valutazione.get_worksheet(4).batch_update(batch_ws4)

        # FOGLIO 2: ARREDAMENTO
        batch_ws2 = []


        for n in coordinate_bagni.keys():
            if arredamento_bagni and n <= int(bagni):
                for cella in coordinate_bagni[n]:
                    batch_ws2.append({'range': cella, 'values': [[True]]})
            else:
                for cella in coordinate_bagni[n]:
                    batch_ws2.append({'range': cella, 'values': [[False]]})

        # LOGICA CAMERE
        mappa_camere = {"singole": camere_singole, "doppie": camere_doppie, "triple": camere_triple}
        for tipo, quantita in mappa_camere.items():
            if arredamento_cam and quantita > 0:
                for cella in coordinate_camere_arredo[tipo]:
                    batch_ws2.append({'range': cella, 'values': [[True]]})
            else:
                for cella in coordinate_camere_arredo[tipo]:
                    batch_ws2.append({'range': cella, 'values': [[False]]})

        # LOGICA CUCINA
        if arredamento_cuc:
            for cella in coordinate_sog_cuc["cucina"]:
                batch_ws2.append({'range': cella, 'values': [[True]]})
        else:
            for cella in coordinate_sog_cuc["cucina"]:
                batch_ws2.append({'range': cella, 'values': [[False]]})

        # LOGICA SOGGIORNO
        if arredamento_sog:
            for cella in coordinate_sog_cuc["soggiorno"]:
                batch_ws2.append({'range': cella, 'values': [[True]]})
        else:
            for cella in coordinate_sog_cuc["soggiorno"]:
                batch_ws2.append({'range': cella, 'values': [[False]]})

        # Invio del batch unico a Google Sheets
        if batch_ws2:
            fogli_di_valutazione.get_worksheet(2).batch_update(batch_ws2)


st.markdown("## Lavori e Stima AI")
lavori = st.text_input("Lavori da fare, escluso arredo di camere/bagni/soggiorno", placeholder="Nessuna stima")


def stimaAI(sas):
    if not sas or sas.strip() == "" or sas == "Nessuna stima":
        return "0"
    modello = gen.GenerativeModel(
        model_name="gemini-3.5-flash",
        system_instruction=f"Sulla base dei seguenti dati:{Indirizzo}/{citta}/ e dei seguenti {sas}, dammi una stima media del costo dei lavori(manodopera inclusa), IVA esclusa. L'output di questo prompt deve essere un numero unico, senza giustificazioni",
        generation_config={"temperature": 0.0})
    risposta = modello.generate_content(sas)
    return risposta.text.strip()


if lavori and lavori.strip() != "":
    costo_stimato = stimaAI(lavori)
    fogli_di_valutazione.get_worksheet(1).update_acell("B14", costo_stimato)
    fogli_di_valutazione.get_worksheet(1).update_acell("A14", lavori)
    st.markdown(f"**La stima dei lavori è di {costo_stimato} euro, è già stata contabilizzata nella valutazione**")
else:
    st.info("Nessun lavoro inserito. Inserisci una descrizione per richiedere la stima AI.")


st.markdown("**GIUDIZIO QUALITATIVO**")
st.markdown("""**Stima istantanea del canone passivo proponibile o pricing delle camere**, 
la stima del canone proponibile produrrà una soglia minima sotto cui tassativamente non si può scendere""")
stima = st.button("Stima")

st.markdown(
    "**Scegliere una delle due opzioni, l'altro dato deve essere disponibile e imputato precedentemente nella pagina**")
col1, col2 = st.columns(2)
with col1:
    canone_nonpresente = st.checkbox("Si vuole ottimizzare per il canone?")
with col2:
    affitti_nonpresenti = st.checkbox("Si vuole ottimizzare per gli affitti")


def ottimizzacanonepassivo(durata_contratto):
    Inserimento_dati.update_acell("B23", 0)
    canone_min = 0
    canone_max = 5000
    canone_ottimale = canone_min
    opzioni_contratto = {1: fogli_di_valutazione.get_worksheet(7), 8: fogli_di_valutazione.get_worksheet(8),
                         12: fogli_di_valutazione.get_worksheet(9), 16: fogli_di_valutazione.get_worksheet(10)}

    def pulisci_valore(val_str):
        if val_str is None:
            return 0.0
        s = str(val_str).strip().replace(" ", "").replace("€", "")
        ha_percentuale = "%" in s
        if ha_percentuale:
            s = s.replace("%", "")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            valore_float = float(s)
            if ha_percentuale:
                valore_float = valore_float / 100.0
            return valore_float
        except ValueError:
            return 0.0

    def leggi_valori(durata_contratto):
        val_roi = pulisci_valore(opzioni_contratto[durata_contratto].acell("AM15").value)
        val_capex = pulisci_valore(opzioni_contratto[durata_contratto].acell("AE15").value)
        val_utile = pulisci_valore(opzioni_contratto[durata_contratto].acell("AM11").value)
        return val_roi, val_capex, val_utile

    margine_errore = 20
    soglia_roi = 1.5
    soglia_capex = 0.2
    soglia_utile = 1000
    durata_ricerca = 8 if durata_contratto == 0 else durata_contratto

    while (canone_max - canone_min) > margine_errore:
        canone_test = (canone_min + canone_max) / 2.0
        Inserimento_dati.update_acell("B23", canone_test)
        time.sleep(2.5)
        val_roi, val_capex, val_utile = leggi_valori(durata_ricerca)
        if val_roi > soglia_roi and val_capex > soglia_capex and val_utile > soglia_utile:
            canone_min = canone_test
            canone_ottimale = canone_test
        else:
            canone_max = canone_test

    Inserimento_dati.update_acell("B23", canone_ottimale)
    return canone_ottimale







if canone_nonpresente and stima:
    risultato_canone_ottimizzato = ottimizzacanonepassivo(durata_contrattuale)
    st.markdown(f"Il canone stimato è di {risultato_canone_ottimizzato}")


def ottimizzacanoneattivo(durata_contratto):
    fogli_di_valutazione.get_worksheet(4).update_acell("H2", 0)
    canone_min = 0
    canone_max = 5000
    canone = canone_min
    opzioni_contratto = {1: fogli_di_valutazione.get_worksheet(7), 8: fogli_di_valutazione.get_worksheet(8),
                         12: fogli_di_valutazione.get_worksheet(9), 16: fogli_di_valutazione.get_worksheet(10)}

    def pulisci_valore(val_str):
        if val_str is None:
            return 0.0
        s = str(val_str).strip().replace(" ", "").replace("€", "")
        ha_percentuale = "%" in s
        if ha_percentuale:
            s = s.replace("%", "")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            valore_float = float(s)
            if ha_percentuale:
                valore_float = valore_float / 100.0
            return valore_float
        except ValueError:
            return 0.0

    def leggi_valori(durata_contratto):
        val_roi = pulisci_valore(opzioni_contratto[durata_contratto].acell("AM15").value)
        val_capex = pulisci_valore(opzioni_contratto[durata_contratto].acell("AE15").value)
        val_utile = pulisci_valore(opzioni_contratto[durata_contratto].acell("AM11").value)
        return val_roi, val_capex, val_utile

    margine_errore = 50
    soglia_roi = 1.5
    soglia_capex = 0.2
    soglia_utile = 1000
    durata_ricerca = 8 if durata_contratto == 0 else durata_contratto

    while (canone_max - canone_min) > margine_errore:
        canone_test = (canone_min + canone_max) / 2.0
        fogli_di_valutazione.get_worksheet(4).update_acell("H3", canone_test)
        time.sleep(2.5)
        val_roi, val_capex, val_utile = leggi_valori(durata_ricerca)
        if val_roi > soglia_roi and val_capex > soglia_capex and val_utile > soglia_utile:
            canone_max = canone_test
            canone = canone_test
        else:
            canone_min = canone_test

    if durata_contratto == 0:
        fogli_di_valutazione.get_worksheet(4).update_acell("H3", canone)
    else:
        Inserimento_dati.update_acell("B23", canone)
    return fogli_di_valutazione.get_worksheet(4).acell("H3").value


if affitti_nonpresenti and stima:
    risultato_affitti_ottimizzati = ottimizzacanoneattivo(durata_contrattuale)
    st.markdown(
        f"**Canone di affitto totale(somma di tutti gli affitti delle camere) stimato {risultato_affitti_ottimizzati}** ")

# STAMPA FINALE MAIL
st.markdown(
    "I dati pre-compilati nel form verranno disposti in modo tale che siano copiabili e incollabili direttamente nella mail da inviare per valutazione")
stampa = st.button("Produci contenuti Mail")
if stampa:
    st.write(f"""Riepilogo dei dati compilati: \n

Link annuncio:  {link_annuncio} \n

Indirizzo (completo di numero civico): {Indirizzo} \n
Città: {citta} \n
Superficie immobile: {metri_quadri} \n
Tipologia riscaldamento (autonomo o centralizzato): {tipologia_riscaldamento} \n
Acqua calda (come viene alimentata): {alimentazione_acqua} \n
Raffrescamento (si/no): {raffrescamento} \n
Piano cottura (gas o induzione): {piano_cottura} \n
Stato attuale dell'appartamento: {stato_attuale} \n
Cucina(numero): {cucina} \n
Soggiorno: {soggiorno} \n
Bagni: {bagni} \n
Camere singole: {camere_singole} \n
Camere doppie: {camere_doppie} \n
Altri locali: {altri_locali} \n
Arredamento camere:  \n
Arredamento bagni: \n
Arredamento cucina: \n
Arredamento soggiorno: \n
Oneri condominiali mensili (senza riscaldamento): € {oneri_condominiali} \n
Acqua compresa negli oneri (si/no): {acqua_compresa_oneri} \n
Riscaldamento compreso negli oneri (se no a quanto ammonta): {riscaldamento_compreso_oneri} \n
Società di Locazione (Homa no cedolare, oppure Rent Hub cedolare al 21% ma solo studenti): {società_di_locazione} \n
Canone mensile richiesto dalla proprietà(se =0 non definito): {canone_mensile} \n
Agenzia (si/no): {agenzia} \n
Fee di Agenzia: {fee_agenzia} \n
Mensilità di deposito cauzionale: {mensilità_deposito} \n
Inizio mese locazione: {inizio_locazione} \n
Mesi di sfitto previsti: {mesi_sfitto} \n
Stima prezzo di uscita (all inclusive di ogni camera): 1 a 450€ e 3 a 500€  \n
Lavori da fare a carico nostro: {lavori} \n
    

""")