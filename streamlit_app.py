# basic imports
import streamlit as st
import pandas as pd

# imports for search console libraries
import searchconsole
from apiclient import discovery
from google_auth_oauthlib.flow import Flow

# imports for aggrid
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid import GridUpdateMode, DataReturnMode

# all other imports
import os

###############################################################################

# The code below is for the layout of the page
if "widen" not in st.session_state:
    layout = "centered"
else:
    layout = "wide" if st.session_state.widen else "centered"

st.set_page_config(
    layout=layout, page_title="Google Search Console Connector", page_icon="🔌"
)

###############################################################################

# row limit
RowCap = 25000

###############################################################################

# Initialisation de l'état de session pour les jetons OAuth
if "gsc_token_input" not in st.session_state:
    st.session_state["gsc_token_input"] = ""
if "gsc_token_received" not in st.session_state:
    st.session_state["gsc_token_received"] = False
if "credentials_fetched" not in st.session_state:
    st.session_state["credentials_fetched"] = None
if "account" not in st.session_state:
    st.session_state["account"] = None
if "site_urls" not in st.session_state:
    st.session_state["site_urls"] = []

# Convert secrets from the TOML file to strings
clientSecret = str(st.secrets["installed"]["client_secret"])
clientId = str(st.secrets["installed"]["client_id"])
redirectUri = str(st.secrets["installed"]["redirect_uris"][0])

###############################################################################

tab1, tab2 = st.tabs(["Main", "About"])

with tab1:

    st.sidebar.image("logo.png", width=290)

    st.sidebar.markdown("")

    st.write("")

    # Instructions pour la récupération du code OAuth
    with st.sidebar:
        st.markdown(
            f"""
            ### Étapes pour vous connecter à la Google Search Console :

            1. [Connectez-vous à GSC](https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={clientId}&redirect_uri={redirectUri}&scope=https://www.googleapis.com/auth/webmasters.readonly&access_type=offline&prompt=consent)
            2. Copiez le code d'autorisation obtenu.
            3. Collez-le ci-dessous et appuyez sur Entrée.
            """
        )

        # Entrée manuelle du code d'autorisation OAuth
        auth_code_input = st.text_input("Entrez le code OAuth de Google", value="", key="auth_code")

        if auth_code_input:
            st.session_state["gsc_token_input"] = auth_code_input
            st.session_state["gsc_token_received"] = True
            st.success("Code d'autorisation reçu.")

    container3 = st.sidebar.container()

    st.sidebar.write("")

    st.sidebar.caption(
        "Made in 🎈 [GitHub](https://www.streamlit.io/), by [Aurélie from Nexus](https://github.com/AurelieNexus), inspired by [Charly Wargnier](https://www.charlywargnier.com/)."
    )

    try:
        # Gestion de l'authentification et récupération des données GSC
        if st.session_state.gsc_token_received:
            if not st.session_state["credentials_fetched"]:
                try:
                    # Configuration du flux OAuth
                    flow = Flow.from_client_config(
                        {
                            "installed": {
                                "client_id": clientId,
                                "client_secret": clientSecret,
                                "redirect_uris": [redirectUri],
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://accounts.google.com/o/oauth2/token",
                            }
                        },
                        scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
                        redirect_uri=redirectUri,
                    )
                    # Échange du code d'autorisation contre les jetons
                    flow.fetch_token(code=st.session_state.gsc_token_input)
                    st.session_state["credentials_fetched"] = flow.credentials

                    # Construction du service Google Search Console
                    service = discovery.build(
                        serviceName="webmasters",
                        version="v3",
                        credentials=st.session_state["credentials_fetched"],
                        cache_discovery=False,
                    )

                    # Création de l'objet de compte Search Console
                    st.session_state["account"] = searchconsole.account.Account(
                        service, st.session_state["credentials_fetched"])

                    # Récupération de la liste des sites
                    site_list = service.sites().list().execute()
                    first_value = list(site_list.values())[0]
                    st.session_state["site_urls"] = [dicts.get("siteUrl") for dicts in first_value if dicts.get("siteUrl")]

                    st.sidebar.info("✔️ Identifiants GSC valides !")
                    st.success("Autorisation réussie.")

                except Exception as e:
                    st.error(f"Une erreur est survenue lors de la récupération des jetons : {str(e)}")
            else:
                pass

            # Vérification que les crédentiels sont disponibles
            if st.session_state["credentials_fetched"]:
                # Formulaire pour la récupération des données
                with st.form(key="gsc_data_form"):
                    # Sélection de la propriété Web
                    selected_site = st.selectbox("Sélectionnez la propriété Web", st.session_state["site_urls"])
                    # ...ajoutez ici le reste de votre formulaire pour gérer les requêtes de données...

                    submit_button = st.form_submit_button("Fetch GSC API data")
                    if submit_button:
                        # Logique pour récupérer et afficher les données de la Search Console...
                        st.write("Récupération des données pour le site sélectionné...")
                        # Reportez-vous ici à votre logique existante pour la récupération des données
                        # et l'affichage utilisant les DataFrames et AgGrid si nécessaire.

    except ValueError as ve:
        st.warning("⚠️ You need to sign in to your Google account first!")

    except IndexError:
        st.info(
            "⛔ It seems you haven’t correctly configured Google Search Console! Click [here](https://support.google.com/webmasters/answer/9008080?hl=en) for more information on how to get started!"
        )

with tab2:

    st.write("")
    st.write("")

    st.write(
        """

    #### About this app

    * ✔️ One-click connect to the [Google Search Console API](https://developers.google.com/webmaster-tools)
    * ✔️ Easily traverse your account hierarchy
    * ✔️ Go beyond the [1K row UI limit](https://www.gsqi.com/marketing-blog/how-to-bulk-export-search-features-from-gsc/)
    * ✔️ Enrich your data querying with multiple dimensions layers and extra filters!

    ✍️ You can read the blog post [here](https://blog.streamlit.io/p/e89fd54e-e6cd-4e00-8a59-39e87536b260/) for more information.

    #### Going beyond the `25K` row limit

    * There's a `25K` row limit per API call on the [Cloud](https://streamlit.io/cloud) version to prevent crashes.
    * You can remove that limit by forking this code and adjusting the `RowCap` variable in the `streamlit_app.py` file

    #### Kudos

    This app relies on Josh Carty's excellent [Search Console Python wrapper](https://github.com/joshcarty/google-searchconsole). Big kudos to him for creating it!

    #### Questions, comments, or report a 🐛?

    * If you have any questions or comments, please DM [me](https://twitter.com/DataChaz). Alternatively, you can ask the [Streamlit community](https://discuss.streamlit.io).
    * If you find a bug, please raise an issue in [Github](https://github.com/CharlyWargnier/google-search-console-connector/pulls).

    #### Known bugs
    * You can filter any dimension in the table even if the dimension hasn't been pre-selected. I'm working on a fix for this.
    
    """
    )
