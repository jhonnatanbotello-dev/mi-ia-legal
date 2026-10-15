import streamlit as st
import sqlite3
from datetime import datetime
import ollama
import smtplib
import io
from pypdf import PdfReader
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 🔑 CONFIGURACIÓN DE TU CORREO
CORREO_EMISOR = "jhonnatanbotello@gmail.com"
CONTRASEÑA_APP = "mjeoqwvzybczzyid"
CORREO_RECEPTOR = "jhonnatanbotello@gmail.com"

def leer_archivo_pdf(archivo):
    try:
        lector = PdfReader(archivo)
        texto = ""
        for pagina in lector.pages: texto += pagina.extract_text()
        return texto
    except Exception: return ""

def enviar_correo_alerta(consulta, respuesta):
    try:
        msg = MIMEMultipart()
        msg['From'] = CORREO_EMISOR
        msg['To'] = CORREO_RECEPTOR
        msg['Subject'] = "📩 Nueva Consulta Legal en tu App"
        cuerpo = f"Se ha registrado una interacción jurídica:\n\n❓ Consulta: {consulta}\n\n🤖 Respuesta del Abogado IA:\n{respuesta}"
        msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
        server = smtplib.SMTP_SSL('://gmail.com', 465)
        server.login(CORREO_EMISOR, CONTRASEÑA_APP)
        server.sendmail(CORREO_EMISOR, CORREO_RECEPTOR, msg.as_string())
        server.quit()
    except Exception: pass

def obtener_contexto_aprendizaje():
    try:
        conn_db = sqlite3.connect('consultas_usuarios.db')
        cursor_db = conn_db.cursor()
        cursor_db.execute("SELECT consulta, respuesta FROM historial ORDER BY id DESC LIMIT 5")
        filas = cursor_db.fetchall()
        conn_db.close()
        if not filas: return ""
        contexto = "\n--- PRECEDENTES Y CONSULTAS GUARDADAS ---\n"
        for con, res in reversed(filas): contexto += f"Cliente: {con}\nAbogado IA: {res}\n\n"
        return contexto + "-----------------------------------------\n"
    except Exception: return ""

# Inicializar Base de Datos
conn = sqlite3.connect('consultas_usuarios.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, consulta TEXT, respuesta TEXT)')
conn.commit()

# Diseño Interfaz Lateral
st.sidebar.title("📁 Documentos de Sustento")
st.sidebar.markdown("Carga archivos de consulta para el análisis:")
pdf_subido = st.sidebar.file_uploader("Subir archivo PDF", type=["pdf"])

if st.sidebar.button("🗑️ Limpiar Pantalla"):
    st.session_state.messages = []

# Área de Chat Principal
st.title("⚖️ Centro IA de Redacción Pro")
st.subheader("Consultoría Legal de Redacción Automatizada - Régimen Peruano")

if "messages" not in st.session_state: st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.markdown(message["content"])

if prompt := st.chat_input("Solicita tu redacción jurídica aquí..."):
    texto_pdf = ""
    if pdf_subido:
        texto_pdf = f"\n[Insumo o Documento adjunto por el cliente]:\n{leer_archivo_pdf(pdf_subido)}\n"
        st.info("📄 Documento cargado para el análisis legal.")
                       # Conexión cifrada directa al cerebro de tu laptop
    client = ollama.Client(host='    client = ollama.Client(host='https://ngrok-free.dev')
')
    
    with st.chat_message("user"): st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            memoria = obtener_contexto_aprendizaje()
            
            instruccion = (
                "Eres un prestigioso Abogado Senior especialista en Derecho Laboral Peruano. Redacta con máxima seriedad, "
                "rigor jurídico, elocuencia y coherencia absoluta. Tienes terminantemente prohibido alucinar, inventar leyes falsas "
                "o usar un lenguaje informal o contradictorio. Redacta las solicitudes bajo los estándares del derecho administrativo "
                "peruano con la siguiente estructura formal:\n"
                "1. SUMILLA (Ej: SOLICITO: Descanso vacacional por 15 días calendario).\n"
                "2. DESTINATARIO (Cargo de la jefatura o Recursos Humanos).\n"
                "3. CUERPO (Breve, formal, solicitando hacer uso físico de tu derecho a descanso vacacional conforme a la programación anual).\n"
                "4. BASE LEGAL (Cita con precisión el Decreto Legislativo N° 713 que regula los descansos remunerados en la actividad privada).\n"
                "5. SECCIÓN DE FIRMA Y DATOS.\n"
                "Sé directo, coherente y jamás incluyas notas explicativas ni introducciones fuera del documento."
            )
            
            mensaje_final = f"{instruccion}\n\n{memoria}{texto_pdf}\nInstrucción actual del cliente: {prompt}"
            
            response = client.chat(model='llama3:8b', messages=[{'role': 'user', 'content': mensaje_final}])
            respuesta_ia = response['message']['content']
            message_placeholder.markdown(respuesta_ia)
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            styles = getSampleStyleSheet()
            estilo = ParagraphStyle('Formal', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=16, spaceAfter=12)
            for linea in respuesta_ia.split('\n'):
                if linea.strip(): story.append(Paragraph(linea.strip(), estilo))
                else: story.append(Spacer(1, 10))
            doc.build(story)
            
            st.download_button(label="📥 Descargar esta redacción en PDF", data=buffer.getvalue(), file_name="redaccion_legal_peru.pdf", mime="application/pdf")
            
        st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
        f_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO historial (fecha, consulta, respuesta) VALUES (?, ?, ?)", (f_actual, prompt, respuesta_ia))
        conn.commit()
        enviar_correo_alerta(prompt, respuesta_ia)
    except Exception as e: st.error(f"Error en la consulta legal: {e}")
