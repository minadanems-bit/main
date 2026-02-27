# ===============================
# PRINTER CONFIG
# ===============================
if "printers" not in db:
    db["printers"] = {
        "Kyocera 3010i": "192.168.1.120",
        "Xerox 7835": "192.168.1.65",
        "Kyocera P5031DN": "192.168.1.126"
    }

PRINTERS = db.get("printers", {}).copy()

   # ==============================
    # 🖨️ Printers Analysis (3 Printers)
    # ==============================
    
    elements.append(Paragraph("🖨️ Printers Analysis", styles['Heading2']))
    printer_diff = st.session_state.get("printer_diff", {})
    
    kyo3010 = printer_diff.get("Kyocera 3010i", {})
    xerox7835 = printer_diff.get("Xerox 7835", {})
    p5031 = printer_diff.get("Kyocera P5031DN", {})
    # --------- KYOCERA 3010i ----------
    k1 = kyo3010.get("1s", 0)
    k2 = kyo3010.get("2s", 0)
    kjam = kyo3010.get("jam", 0)
    
    # --------- XEROX 7835 ----------
    x1 = xerox7835.get("1s", 0)
    x2 = xerox7835.get("2s", 0)
    xjam = xerox7835.get("jam", 0)
    
    # --------- KYOCERA P5031DN ----------
    p1 = p5031.get("1s", 0)
    p2 = p5031.get("2s", 0)
    pjam = p5031.get("jam", 0)
    
    prn_data = [
        ["Machine", "Total Used", "Paper Jam", "1-Sided", "2-Sided"],
        
        [
            "Kyocera 3010i",
            k1 + k2,
            kjam,
            k1,
            k2
        ],
    
        [
            "Xerox 7835",
            x1 + x2,
            xjam,
            x1,
            x2
        ],
    
        [
            "Kyocera P5031DN",
            p1 + p2,
            pjam,
            p1,
            p2
        ]
    ]
    
    prn_table = Table(prn_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 2*inch, 2*inch])
    
    prn_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkred),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    elements.append(prn_table)
    elements.append(Spacer(1, 20))
    
    doc.build(elements)
    return buffer.getvalue()


def calculate_printer_difference(start_data, end_data):
    diff = {}

    for printer in start_data:
        diff[printer] = {}

        fields = ["Total", "One Side", "Two Side", "Errors", "Jam"]

        for field in fields:
            try:
                start_value = int(start_data[printer].get(field, 0) or 0)
                end_value = int(end_data[printer].get(field, 0) or 0)

                diff[printer][field] = end_value - start_value
            except:
                diff[printer][field] = 0

    return diff   # 🔥 هنا بس النهاية


# --- 3. Session Setup ---
st.set_page_config(page_title="NMS ERP Platinum", layout="wide", page_icon="🚀")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None})

def sync_draft():
    if st.session_state['logged_in']:
        user = st.session_state['user']
        draft_keys = ('s_','o_','e_','c_','m_','i_','ks','xs','op','u10','v22','ex','kj','xj','dn','k1','k2','x1','x2')
        draft_data = {k: v for k, v in st.session_state.items() if k.startswith(draft_keys)}
        if "drafts" not in db: db["drafts"] = {}
        db["drafts"][user] = draft_data
        save_db(db)
