import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# Configuración
st.set_page_config(page_title="Digitalex: Salva la Empresa", layout="wide")

# --- CONFIGURACIÓN DE GMAIL ---
GMAIL_USER = "torsa.innovalab@gmail.com"       # 👈 ¡CAMBIA ESTE CORREO!
GMAIL_APP_PASSWORD = "hqku owad pyko hiwp"     # 👈 ¡CAMBIA ESTA CONTRASEÑA DE APLICACIÓN!

# --- CONFIGURACIÓN DE GOOGLE SHEETS ---
SHEET_ID = "13d3Z30ycOvrRaPHpQveGP0v8QSo9nYcR99CrHa7rHXI"        # 👈 ¡CAMBIA ESTE ID POR EL TUYO!
CREDENTIALS_FILE = "digitalexranking-80fa195c3e5f.json"  # 👈 ¡ASEGÚRATE DE QUE ESTÉ EN LA MISMA CARPETA!

# --- CONFIGURACIÓN DE LOGIN DOCENTE ---
ADMIN_PASSWORD = "Docentejwts"  # 👈 ¡CAMBIA ESTA CONTRASEÑA POR UNA SEGURA!

# --- INICIALIZAR SESIONES ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "step" not in st.session_state:
    st.session_state.step = "welcome"

# --- FUNCIÓN PARA GENERAR PDF DEL CERTIFICADO ---
def generar_certificado_pdf(nombre, email, resultado):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=1,
        textColor=colors.darkgreen
    )
    normal_style = styles['Normal']
    bold_style = ParagraphStyle(
        'Bold',
        parent=normal_style,
        fontSize=12,
        fontWeight='bold'
    )

    story = []

    # Título
    story.append(Paragraph("🎉 CERTIFICADO DE LOGRO 🎉", title_style))
    story.append(Spacer(1, 20))

    # Contenido
    story.append(Paragraph(f"<b>Nombre:</b> {nombre}", bold_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Email:</b> {email}", bold_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>Logros alcanzados en Digitalex:</b>", bold_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"- Tasa de Conversión Final: <b>{resultado['conversion']:.1f}%</b>", normal_style))
    story.append(Paragraph(f"- Reducción de Rebote: <b>{78 - resultado['rebote']} puntos</b>", normal_style))

    # Cancelaciones con color dinámico
    status_text = "🌟 Excelente retención" if resultado['cancelacion'] <= 8 else "🟡 Mejora posible"
    color = "#2E8B57" if resultado['cancelacion'] <= 8 else "#FFA500"
    story.append(Paragraph(f"- Tasa de Cancelación: <b>{resultado['cancelacion']}%</b> → <font color='{color}'>{status_text}</font>", normal_style))

    story.append(Paragraph(f"- Engagement Promedio: <b>{resultado['engagement']:.1f} min</b>", normal_style))
    story.append(Paragraph(f"- Visitantes Totales: <b>{resultado['visitantes']:,}</b>", normal_style))
    story.append(Spacer(1, 20))

    # Score con color verde
    score = calcular_puntaje(resultado)
    story.append(Paragraph(f"<b>Puntaje de Salvación: <font color='#2E8B57'>{score}/100</font></b>", bold_style))
    story.append(Spacer(1, 20))

    # Pie
    story.append(Paragraph("Has aprendido que no se trata de más clicks… sino de más conexiones humanas.", normal_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Certificado emitido el {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Italic']))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- FUNCIÓN PARA CALCULAR EL PUNTAJE (0-100) ---
def calcular_puntaje(resultado):
    score = 0
    conv_score = min(40, max(0, (resultado['conversion'] - 0.5) * 20))
    score += conv_score
    rebote_score = min(30, max(0, (78 - resultado['rebote']) * 1.5))
    score += rebote_score
    cancel_score = min(20, max(0, (15 - resultado['cancelacion']) * 4))
    score += cancel_score
    eng_score = min(10, max(0, (resultado['engagement'] - 0.5) * 6.67))
    score += eng_score
    return round(score)

# --- FUNCIÓN PARA ENVIAR EMAIL CON PDF ---
def enviar_certificado_por_email(nombre, email, resultado):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = email
        msg['Subject'] = f"🎉 Certificado: Maestro de la Analítica Digital - Digitalex"

        body = f"""
        ¡Felicidades, {nombre}!

        Has completado el taller "Digitalex: Salva la Empresa" con éxito.
        
        Logros:
        - Tasa de Conversión Final: {resultado['conversion']:.1f}%
        - Reducción de Rebote: {78 - resultado['rebote']} puntos
        - Cancelaciones: {resultado['cancelacion']}%
        - Engagement: {resultado['engagement']:.1f} min
        - Puntaje de Salvación: {calcular_puntaje(resultado)}/100
        
        Eres un(a) profesional de marketing digital con habilidades reales.
        
        Con cariño,
        Prof. Wilton Torvisco
        Curso: Marketing Digital y Analítica Web
        Universidad Privada del Norte
        """
        
        msg.attach(MIMEText(body, 'plain'))

        pdf_data = generar_certificado_pdf(nombre, email, resultado)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_data)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{nombre.replace(" ", "_")}_Certificado_Digitalex.pdf"'
        )
        msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        clean_password = GMAIL_APP_PASSWORD.replace(" ", "")
        server.login(GMAIL_USER, clean_password)
        text = msg.as_string()
        server.sendmail(GMAIL_USER, email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"🚨 ERROR DETALLADO: {str(e)}")
        return False

# --- FUNCIÓN PARA GUARDAR EN GOOGLE SHEETS ---
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def init_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    return sheet

def guardar_en_sheet(nombre, email, puntaje, conversion, rebote, cancelacion, engagement, visitantes):
    try:
        sheet = init_sheet()
        row = [nombre, email, puntaje, conversion, rebote, cancelacion, engagement, visitantes, datetime.now().strftime("%d/%m/%Y %H:%M")]
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"❌ Error guardando en Google Sheets: {e}")
        return False

def obtener_ranking():
    try:
        sheet = init_sheet()
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"❌ Error leyendo Google Sheets: {e}")
        return pd.DataFrame()

# --- FUNCIÓN PARA OBTENER ACCIONES DINÁMICAS SEGÚN RETOS ---
def obtener_acciones_disponibles(metricas):
    acciones = []
    
    if metricas['rebote'] > 70:
        acciones.extend([
            "Cambiar el botón 'Comprar' por '¡Quiero ser parte del cambio!'",
            "Agregar testimonios reales de clientes en la landing",
            "Publicar video de la artesana que cose las prendas",
            "Mostrar infografía interactiva: ‘De la semilla a tu armario’",
            "Incluir testimonio en video de 15 seg de una artesana quechua"
        ])
    
    if metricas['conversion'] < 2:
        acciones.extend([
            "Reducir pasos del checkout de 5 a 3",
            "Enviar email de bienvenida con 10% de descuento",
            "Agregar sello ‘Certificación de Comercio Justo’",
            "Mostrar garantía de devolución gratuita + 100 días",
            "Publicar certificados de impacto ambiental (CO2 ahorrado por prenda)"
        ])
    
    if metricas['cancelacion'] > 10:
        acciones.extend([
            "Implementar chatbot 24/7 para dudas",
            "Crear quiz: ‘¿Qué tipo de sostenibilidad eres?’",
            "Enviar ‘Carta de Agradecimiento’ personalizada por correo tras la compra",
            "Crear programa ‘Amigo Sostenible’: invita a un amigo y ambos reciben 15% de descuento",
            "Publicar mensualmente ‘El Diario de la Artisana’ — blog emocional"
        ])
    
    if metricas['rebote'] <= 60 and metricas['conversion'] >= 2.5 and metricas['cancelacion'] <= 8:
        acciones.extend([
            "Lanzar colección limitada con artistas locales",
            "Crear NFT de autenticidad de cada prenda",
            "Invitar a influencers sostenibles a vivir 1 semana con la artesana"
        ])
    
    acciones = list(set(acciones))[:7]
    return acciones

# --- BIENVENIDA ---
if st.session_state.step == "welcome":
    st.title("🚨 ¡URGENTE! La startup Digitalex está en crisis...")
    st.markdown("""
        ### 🌱 Contexto Real: Digitalex
        Digitalex es una startup peruana de moda sostenible que vende ropa hecha con algodón orgánico y tejidos reciclados, producida por artesanas andinas con pago justo.  
        Su modelo es direct-to-consumer (DTC).  
        **Problema crítico:**  
        Tiene 15,000 visitantes/semana, pero solo 180 compras.  
        El 78% abandona en la landing page.  
        El 12% cancela su suscripción mensual por no sentir conexión con la marca.  
        
        **Tu misión como equipo de Marketing Digital:**  
        Transformar a Digitalex de una tienda con tráfico... en una marca con comunidad.  
        **Tienes 40 minutos para salvarla antes de que el CEO cierre la empresa.**  
        No hay tiempo para teoría. Solo datos. Solo decisiones.  
        💡 Usa las métricas como tu brújula. ¿Adquieres? ¿Conviertes? ¿Retienes?
    """)
    if st.button("➡️ Entrar al Panel de Control", type="primary"):
        st.session_state.step = "metrics"

# --- CARTAS DE MÉTRICAS ---
elif st.session_state.step == "metrics":
    st.title("🪄 Las 7 Cartas de Poder: Conoce tus métricas")
    st.caption("Haz clic en cada una para entender su impacto real")

    metrics_info = {
        "🚩 Tasa de Visitantes": {
            "def": "Número único de personas que llegan a tu sitio.",
            "why": "Sin tráfico, no hay negocio. Pero más visitas ≠ más ventas.",
            "alert": "⚠️ Si < 5K/semana, revisa tus canales (SEO, ads, redes).",
            "example": "Un estudiante aumentó visitas 40% con TikTok Ads enfocadas en millennials eco-conscientes."
        },
        "🏃‍♂️ Tasa de Rebote": {
            "def": "% de usuarios que salen tras ver solo una página.",
            "why": "Si el 78% se va rápido, tu landing page no conecta.",
            "alert": "❌ Peligro: >70% = diseño, mensaje o carga malos.",
            "example": "Cambiar ‘Compra ahora’ por ‘Únete a la revolución verde’ bajó rebote del 78% al 59%."
        },
        "💰 Tasa de Conversión": {
            "def": "% de visitantes que completan la acción deseada (compra, registro, descarga).",
            "why": "Aquí gana o pierde la empresa. Si es <2%, algo falla en el funnel.",
            "alert": "📉 <1.5% = problema en precio, confianza o proceso.",
            "example": "Añadir sellos de seguridad y garantías aumentó conversión de 1.2% a 2.8%."
        },
        "❤️ Tasa de Engagement": {
            "def": "Tiempo promedio en el sitio y páginas vistas por sesión.",
            "why": "Si están 1 minuto y ven 1 página… no les importas.",
            "alert": "⏳ <1.5 min = contenido poco relevante o aburrido.",
            "example": "Videos de artesanas aumentaron engagement de 1.1 a 2.4 min."
        },
        "🚪 Tasa de Salida": {
            "def": "% que abandonan desde una página específica (ej. carrito).",
            "why": "No es rebote: estaban navegando. ¿Por qué se van justo aquí?",
            "alert": "❗ Alta en checkout = problemas de pago, costos de envío, o formularios largos.",
            "example": "Reducir campos del formulario de pago de 7 a 3 aumentó ventas un 32%."
        },
        "❌ Tasa de Cancelación": {
            "def": "% de clientes que dejan de comprar (suscripciones o compras recurrentes).",
            "why": "Retener cuesta 5x menos que adquirir. Si cancelan mucho, no ganas.",
            "alert": "🔥 >10%/mes = mala experiencia post-compra o falta de valor continuo.",
            "example": "Enviar un email con consejos de cuidado de la ropa redujo cancelaciones del 15% al 7%."
        },
        "🔁 Adquirir, Convertir, Retener (ACR)": {
            "def": "El triángulo sagrado del marketing digital.",
            "why": "Si gastas 80% en adquirir y 5% en retener, estás construyendo un castillo de arena.",
            "alert": "⚠️ Desbalance = gasto innecesario. La lealtad es tu ventaja competitiva.",
            "example": "Netflix gana porque retiene. Amazon gana porque vuelve a vender. ¿Y tú?"
        }
    }

    for title, info in metrics_info.items():
        with st.expander(title):
            st.write(f"**Definición:** {info['def']}")
            st.write(f"**¿Por qué importa?** {info['why']}")
            st.warning(info['alert'])
            st.info(f"💡 Ejemplo real: {info['example']}")
            if st.button(f"¡Lo vi en mi trabajo! 👇", key=title):
                st.success("¡Excelente! Cuéntalo en el chat de Zoom. ¡Vamos a aprender juntos!")

    if st.button("➡️ Ir a la Simulación", type="primary"):
        st.session_state.step = "simulation"

# --- SIMULACIÓN ---
elif st.session_state.step == "simulation":
    st.title("🛠️ Panel de Control: Toma Tus Decisiones")

    metricas = {
        "visitantes": 15000,
        "rebote": 78,
        "conversion": 1.2,
        "engagement": 1.1,
        "cancelacion": 12
    }

    st.subheader("📊 Situación Actual - Semana 1")
    col1, col2, col3 = st.columns(3)
    col1.metric("Visitantes", f"{metricas['visitantes']:,}")
    col2.metric("Tasa de Rebote", f"{metricas['rebote']}%", delta="+12%")
    col3.metric("Tasa de Conversión", f"{metricas['conversion']:.1f}%", delta="-0.8%")
    st.metric("Engagement", f"{metricas['engagement']} min", delta="-0.1 min")
    st.metric("Cancelaciones", f"{metricas['cancelacion']}%", delta="+2%")

    if metricas['rebote'] > 70:
        st.warning("⚠️ **RETO ACTIVO: Alta tasa de rebote (78%) — Tu landing page no conecta emocionalmente.**")
    if metricas['conversion'] < 2:
        st.warning("⚠️ **RETO ACTIVO: Baja tasa de conversión (1.2%) — Falta confianza en la marca.**")
    if metricas['cancelacion'] > 10:
        st.warning("⚠️ **RETO ACTIVO: Alta cancelación (12%) — Los clientes no se sienten parte de la comunidad.**")

    acciones = obtener_acciones_disponibles(metricas)
    seleccionadas = st.multiselect("Elige 3 acciones para mejorar (solo 3!):", options=acciones, max_selections=3)

    if len(seleccionadas) == 3:
        if st.button("🚀 APLICAR ACCIONES Y VER RESULTADOS (Semana 2)", type="primary"):
            def simular_acciones(acciones_selec):
                m = metricas.copy()
                impactos = {
                    "Cambiar el botón 'Comprar' por '¡Quiero ser parte del cambio!'": {"rebote": -8, "conversion": +0.8},
                    "Agregar testimonios reales de clientes en la landing": {"rebote": -10, "conversion": +0.7, "engagement": +0.3},
                    "Reducir pasos del checkout de 5 a 3": {"conversion": +1.2},
                    "Enviar email de bienvenida con 10% de descuento": {"conversion": +0.5, "cancelacion": -2},
                    "Crear quiz: '¿Qué tipo de sostenibilidad eres?'": {"visitantes": +2000, "engagement": +0.8, "rebote": -5},
                    "Implementar chatbot 24/7 para dudas": {"cancelacion": -3, "engagement": +0.4},
                    "Publicar video de la artesana que cose las prendas": {"conversion": +0.9, "engagement": +0.6},
                    "Mostrar infografía interactiva: ‘De la semilla a tu armario’": {"rebote": -12, "engagement": +0.7},
                    "Incluir testimonio en video de 15 seg de una artesana quechua": {"conversion": +0.6, "engagement": +0.5},
                    "Agregar sello ‘Certificación de Comercio Justo’": {"conversion": +0.9},
                    "Mostrar garantía de devolución gratuita + 100 días": {"conversion": +0.8},
                    "Publicar certificados de impacto ambiental (CO2 ahorrado por prenda)": {"conversion": +0.7, "engagement": +0.6},
                    "Enviar ‘Carta de Agradecimiento’ personalizada por correo tras la compra": {"cancelacion": -4, "engagement": +0.5},
                    "Crear programa ‘Amigo Sostenible’: invita a un amigo y ambos reciben 15% de descuento": {"visitantes": +1500, "conversion": +0.6, "cancelacion": -3},
                    "Publicar mensualmente ‘El Diario de la Artisana’ — blog emocional": {"cancelacion": -5, "engagement": +1.0},
                    "Lanzar colección limitada con artistas locales": {"visitantes": +3000, "conversion": +1.0},
                    "Crear NFT de autenticidad de cada prenda": {"conversion": +0.8, "engagement": +0.9},
                    "Invitar a influencers sostenibles a vivir 1 semana con la artesana": {"visitantes": +5000, "conversion": +1.2}
                }
                for acc in acciones_selec:
                    if acc in impactos:
                        for k, v in impactos[acc].items():
                            if k in m:
                                m[k] += v
                m["rebote"] = max(40, min(90, m["rebote"]))
                m["conversion"] = max(0.5, min(5, m["conversion"]))
                m["cancelacion"] = max(5, min(20, m["cancelacion"]))
                m["engagement"] = max(0.5, min(4, m["engagement"]))
                return m

            resultado = simular_acciones(seleccionadas)
            st.session_state.resultado = resultado
            st.session_state.step = "results"
            st.rerun()

# --- RESULTADOS Y CERTIFICADO ---
elif st.session_state.step == "results":
    resultado = st.session_state.resultado
    st.title("🎉 ¡FELICIDADES! HAS TOMADO DECISIONES QUE CAMBIARON LA HISTORIA")

    st.subheader("📈 RESULTADO SEMANA 2")
    col1, col2, col3 = st.columns(3)
    col1.metric("Visitantes", f"{resultado['visitantes']:,}", delta=f"+{resultado['visitantes']-15000}")
    col2.metric("Tasa de Rebote", f"{resultado['rebote']}%", delta=f"{resultado['rebote']-78}%")
    col3.metric("Tasa de Conversión", f"{resultado['conversion']:.1f}%", delta=f"{resultado['conversion']-1.2:.1f}%")
    st.metric("Engagement", f"{resultado['engagement']:.1f} min", delta=f"{resultado['engagement']-1.1:.1f} min")
    st.metric("Cancelaciones", f"{resultado['cancelacion']}%", delta=f"{resultado['cancelacion']-12}%")

    score = calcular_puntaje(resultado)
    st.subheader(f"🏆 Tu Puntaje de Salvación: **{score}/100**")

    if score >= 85:
        st.balloons()
        st.success("✨ ¡EXCELENTE! ERES UN MAESTRO DE LA ANALÍTICA DIGITAL. ¡Tu estrategia es impecable!")
    elif score >= 70:
        st.success("👏 ¡MUY BUENO! Tienes un gran entendimiento de las métricas clave.")
    elif score >= 50:
        st.info("👍 ¡BUEN TRABAJO! Ya sabes cómo interpretar los datos.")
    else:
        st.warning("🔄 ¡Tienes potencial! Revisa tus decisiones y vuelve a intentarlo.")

    st.subheader("📜 Tu Certificado Digital")
    nombre = st.text_input("Ingresa tu nombre completo:", placeholder="Ej: Elizabeth Ramos")
    email = st.text_input("Ingresa tu correo institucional o personal:", placeholder="Ej: elizabeth.ramos@gmail.com")

    if nombre and email:
        st.markdown(f"""
            ## 🎖️ CERTIFICADO DE LOGRO  
            **Nombre:** {nombre}  
            **Email:** {email}  
            **Logros:**  
            - Tasa de Conversión: **{resultado['conversion']:.1f}%**  
            - Reducción de Rebote: **{78 - resultado['rebote']} puntos**  
            - Cancelaciones: **{resultado['cancelacion']}%** → {'🌟 Excelente retención' if resultado['cancelacion'] <= 8 else '🟡 Mejora posible'}  
            - Engagement: **{resultado['engagement']:.1f} min**  
            - Visitantes: **{resultado['visitantes']:,}**  
            - 🔥 **Puntaje de Salvación: {score}/100**  
            *Has aprendido que no se trata de más clicks… sino de más conexiones humanas.*  
        """)

        if st.button("📤 ENVIAR CERTIFICADO POR CORREO", type="primary"):
            with st.spinner("Generando y enviando tu certificado..."):
                success = enviar_certificado_por_email(nombre, email, resultado)
                if success:
                    if guardar_en_sheet(
                        nombre=nombre,
                        email=email,
                        puntaje=score,
                        conversion=resultado['conversion'],
                        rebote=resultado['rebote'],
                        cancelacion=resultado['cancelacion'],
                        engagement=resultado['engagement'],
                        visitantes=resultado['visitantes']
                    ):
                        st.success(f"✅ ¡Tu certificado ha sido enviado y registrado en el ranking global!")
                        st.balloons()
                    else:
                        st.warning("⚠️ Certificado enviado, pero no pudimos registrar tu resultado en el ranking. Contacta al docente.")
                else:
                    st.error("❌ Hubo un error al enviar el correo. Verifica tu configuración de Gmail o inténtalo más tarde.")

    else:
        st.info("📝 Por favor ingresa tu nombre y correo para recibir tu certificado.")

    if st.button("🔄 Volver al inicio"):
        st.session_state.step = "welcome"

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666; font-size: 0.8rem;'>© 2025 Desarrollado por Wilton Torvisco — Todos los derechos reservados. Este simulador es propiedad académica del curso de Marketing Digital y Analítica Web.</p>", unsafe_allow_html=True)

# --- LOGIN DOCENTE Y RANKING EN TIEMPO REAL ---
with st.sidebar:
    st.markdown("---")
    st.subheader("🔐 Acceso Docente")

    if not st.session_state.logged_in:
        password_input = st.text_input("Contraseña docente:", type="password", key="admin_password_input")
        if st.button("🔓 Ingresar como Docente"):
            if password_input == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.success("✅ Acceso concedido. Bienvenido, docente.")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")

    if st.session_state.logged_in:
        st.markdown("---")
        st.subheader("📊 Ranking en Tiempo Real (Google Sheets)")
        
        with st.spinner("Actualizando ranking..."):
            df_ranking = obtener_ranking()
        
        if len(df_ranking) > 0:
            df_ranking = df_ranking.sort_values("puntaje", ascending=False).reset_index(drop=True)
            df_ranking.index += 1
            
            st.dataframe(
                df_ranking[["nombre", "puntaje", "conversion", "rebote", "cancelacion", "fecha"]],
                use_container_width=True,
                column_config={
                    "nombre": "Estudiante",
                    "puntaje": st.column_config.NumberColumn("Puntaje (0-100)", format="%d"),
                    "conversion": st.column_config.NumberColumn("Conversión (%)", format="%.1f%%"),
                    "rebote": st.column_config.NumberColumn("Rebote (%)", format="%.0f%%"),
                    "cancelacion": st.column_config.NumberColumn("Cancelación (%)", format="%.0f%%"),
                    "fecha": "Fecha"
                }
            )
            st.info(f"👥 **Total de estudiantes evaluados: {len(df_ranking)}**")
            
            csv = df_ranking.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar Ranking a CSV",
                data=csv,
                file_name=f"ranking_digitalex_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
        else:
            st.write(" aún no hay resultados.")
        
        if st.button("🚪 Salir de modo docente"):
            st.session_state.logged_in = False
            st.rerun()