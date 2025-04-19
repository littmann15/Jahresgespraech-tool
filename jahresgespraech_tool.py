
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from fpdf import FPDF
import base64

# Kompetenzen
kompetenzen = {
    "Teamfähigkeit": "Kooperation im Team, Unterstützung von Kolleg:innen.",
    "Kommunikation": "Klarheit, aktives Zuhören, konstruktives Feedback.",
    "Eigenverantwortung": "Selbstständiges Arbeiten, Zuverlässigkeit.",
    "Innovation": "Ideen einbringen, Veränderungen initiieren.",
    "Fachwissen": "Kenntnisse im eigenen Fachgebiet, Aktualität.",
    "Kundenorientierung": "Bedürfnisse erkennen, Servicegedanke.",
    "Zielorientierung": "Priorisierung, Verbindlichkeit, Umsetzungskraft.",
    "Problemlösung": "Analytisches Denken, effektive Lösungen finden.",
    "Zeitmanagement": "Effiziente Planung, fristgerechtes Arbeiten.",
    "Verantwortungsbewusstsein": "Pflichtgefühl, Verlässlichkeit, Integrität."
}

erfuellungsgrade = {
    "0%": 0,
    "25%": 1,
    "50%": 2,
    "75%": 3,
    "100%": 4
}

def fragebogen(name):
    st.header(f"Fragebogen – {name}")
    bewertung = {}
    for k, beschreibung in kompetenzen.items():
        st.subheader(k)
        st.caption(beschreibung)
        wert = st.selectbox(f"{name} – {k}:", list(erfuellungsgrade.keys()), key=f"{name}_{k}")
        bewertung[k] = erfuellungsgrade[wert]
    return bewertung

def spinnennetz(selbst, fremd):
    labels = list(selbst.keys())
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    selbst_values = list(selbst.values()) + [list(selbst.values())[0]]
    fremd_values = list(fremd.values()) + [list(fremd.values())[0]]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.plot(angles, selbst_values, label="Selbstwahrnehmung", linewidth=2)
    ax.fill(angles, selbst_values, alpha=0.25)
    ax.plot(angles, fremd_values, label="Fremdwahrnehmung", linewidth=2)
    ax.fill(angles, fremd_values, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_ylim(0, 4)
    ax.legend(loc='upper right')
    st.pyplot(fig)
    return fig

def differenzen(selbst, fremd):
    return {k: abs(selbst[k] - fremd[k]) for k in selbst}

def differenzen_anzeigen(selbst, fremd):
    diffs = differenzen(selbst, fremd)
    sortiert = sorted(diffs.items(), key=lambda x: x[1], reverse=True)
    st.subheader("Größte Unterschiede")
    for k, d in sortiert:
        if d > 0:
            st.write(f"**{k}**: Unterschied von {d} Punkten")

def export_csv(df):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("CSV-Export", csv, "jahresgespraech.csv", "text/csv")

def export_pdf(df, diffs, chart_fig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Jahresgespräch – Auswertung", ln=1, align='C')
    pdf.ln(10)

    for index, row in df.iterrows():
        pdf.cell(0, 10, f"{row['Kompetenz']}: Selbst={row['Selbstwahrnehmung']}, Fremd={row['Fremdwahrnehmung']}", ln=1)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Größte Unterschiede:", ln=1)

    for k, d in sorted(diffs.items(), key=lambda x: x[1], reverse=True):
        if d > 0:
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"{k}: Unterschied von {d} Punkten", ln=1)

    img_buffer = BytesIO()
    chart_fig.savefig(img_buffer, format='PNG')
    img_buffer.seek(0)
    pdf.image(img_buffer, x=10, y=None, w=180)

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    b64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="jahresgespraech.pdf">PDF-Export herunterladen</a>'
    st.markdown(href, unsafe_allow_html=True)

# Hauptlogik
st.title("Jahresgespräch: Selbst- und Fremdwahrnehmung")

mitarbeiter = fragebogen("Mitarbeiter")
vorgesetzter = fragebogen("Vorgesetzter")

if st.button("Auswertung anzeigen"):
    df = pd.DataFrame({
        "Kompetenz": list(kompetenzen.keys()),
        "Selbstwahrnehmung": list(mitarbeiter.values()),
        "Fremdwahrnehmung": list(vorgesetzter.values())
    })
    st.subheader("Numerische Übersicht")
    st.dataframe(df.set_index("Kompetenz"))

    chart_fig = spinnennetz(mitarbeiter, vorgesetzter)
    diffs = differenzen(mitarbeiter, vorgesetzter)
    differenzen_anzeigen(mitarbeiter, vorgesetzter)

    export_csv(df)
    export_pdf(df, diffs, chart_fig)
