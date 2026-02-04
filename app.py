from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
import io
import os

app = Flask(__name__)
CORS(app)

class PDFProcessor:
    @staticmethod
    def clean_pdf(input_stream, custom_name="documento_limpio"):
        # Abrimos el PDF desde la memoria
        doc = fitz.open(stream=input_stream, filetype="pdf")
        new_doc = fitz.open()

        for page in doc:
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            page_dict = page.get_text("dict")
            
            for block in page_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            content = span["text"]
                            if not content or not content.strip():
                                continue
                            
                            font_name = "helv"
                            if "bold" in span["font"].lower(): font_name = "hebo"
                            if "italic" in span["font"].lower(): font_name = "heit"

                            try:
                                new_page.insert_text(
                                    span["origin"],
                                    content,
                                    fontsize=span["size"],
                                    fontname=font_name,
                                    color=(0, 0, 0)
                                )
                            except:
                                continue

        # Agregamos el nombre personalizado a los metadatos internos del PDF
        new_doc.set_metadata({
            "title": custom_name,
            "producer": "InkSaver SaaS"
        })

        output_stream = io.BytesIO()
        new_doc.save(output_stream)
        output_stream.seek(0)
        
        doc.close()
        new_doc.close()
        return output_stream

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No se subió ningún archivo"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    # --- NUEVA LÓGICA DE NOMBRE ---
    # 1. Obtenemos el nombre del campo 'output_name' que enviará el Frontend
    # 2. Si viene vacío, usamos el nombre original del archivo (sin el .pdf)
    base_filename = os.path.splitext(file.filename)[0]
    output_name = request.form.get('output_name', base_filename).strip()

    # Si el usuario dejó el campo vacío, volvemos al original
    if not output_name:
        output_name = base_filename

    # Limpiamos el nombre de caracteres que puedan romper el sistema de archivos
    safe_name = "".join(c for c in output_name if c.isalnum() or c in (' ', '_', '-')).strip()
    final_filename = f"{safe_name}.pdf"

    try:
        # Procesar enviando también el nombre para los metadatos
        processed_pdf = PDFProcessor.clean_pdf(file.read(), custom_name=safe_name)
        
        return send_file(
            processed_pdf,
            as_attachment=True,
            download_name=final_filename, # El navegador descargará el archivo con este nombre
            mimetype='application/pdf'
        )
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "No se pudo procesar el archivo"}), 500

if __name__ == '__main__':
    # Importante: para Render o local, el puerto 5000 es el estándar
    app.run(debug=True, port=5000)