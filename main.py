from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfMerger
from io import BytesIO
import base64
import logging

app = FastAPI(
    title="Unificador de PDFs",
    description="""
API para unir múltiples archivos PDF en uno solo.  
Ideal para integraciones con Power Automate, SharePoint, sistemas documentales o flujos automatizados.  
Desarrollado por Danny, arquitecto de soluciones Power Platform.
""",
    version="1.0.0",
    contact={
        "name": "Danny",
        "email": "alex15_25@hotmail.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post(
    "/unir-pdfs",
    summary="Unir PDFs desde contenido base64",
    description="Recibe una lista de archivos PDF en base64 y devuelve un único archivo PDF combinado.",
    response_description="Archivo PDF combinado listo para descargar"
)
async def unir_pdfs(request: Request):
    try:
        data = await request.json()
        archivos = data.get("archivos", [])

        if not archivos or not isinstance(archivos, list):
            raise HTTPException(status_code=400, detail="Se requiere una lista de archivos en base64")

        merger = PdfMerger()
        errores = []
        exitosos = []

        for archivo in archivos:
            nombre = archivo.get("nombre")
            contenido = archivo.get("contenido")

            if not nombre or not contenido:
                errores.append(f"{nombre or 'Archivo sin nombre'} (faltan datos)")
                continue

            try:
                pdf_bytes = base64.b64decode(contenido)
                merger.append(BytesIO(pdf_bytes))
                exitosos.append(nombre)
                logger.info(f"Archivo fusionado: {nombre}")
            except Exception as e:
                errores.append(f"{nombre} ({str(e)})")
                logger.error(f"Error con {nombre}: {str(e)}")

        if not exitosos:
            raise HTTPException(status_code=500, detail=f"No se pudo procesar ningún archivo. Errores: {errores}")

        output_pdf = BytesIO()
        merger.write(output_pdf)
        merger.close()
        output_pdf.seek(0)

        # ✅ Opción 1: devolver como base64 (ideal para Power Automate)
        pdf_base64 = base64.b64encode(output_pdf.read()).decode("utf-8")
        return {
            "mensaje": "PDFs fusionados exitosamente",
            "archivos_fusionados": exitosos,
            "errores": errores,
            "pdf_base64": pdf_base64
        }

        # 🧯 Opción 2: devolver como archivo descargable
        # return StreamingResponse(
        #     output_pdf,
        #     media_type="application/pdf",
        #     headers={"Content-Disposition": "attachment; filename=unificado.pdf"}
        # )

    except Exception as e:
        logger.error(f"Error general: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al unir PDFs")
