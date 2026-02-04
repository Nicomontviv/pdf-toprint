import fitz  # PyMuPDF
import io

class PDFProcessor:
    def __init__(self, input_data, is_stream=True):
        """
        Puede recibir una ruta de archivo (string) o un stream de bytes (memoria).
        """
        if is_stream:
            # Si viene de la web, es un stream de bytes
            self.doc = fitz.open(stream=input_data, filetype="pdf")
        else:
            # Si es para prueba local, es una ruta de archivo
            self.doc = fitz.open(input_data)
        
        self.new_doc = fitz.open()

    def clean_and_reconstruct(self, output_name="documento_limpio.pdf"):
        """
        Procesa el documento y devuelve un stream de memoria (BytesIO) 
        con el resultado, incluyendo el nombre en los metadatos.
        """
        for page_index in range(len(self.doc)):
            old_page = self.doc[page_index]
            new_page = self.new_doc.new_page(
                width=old_page.rect.width, 
                height=old_page.rect.height
            )

            page_dict = old_page.get_text("dict")
            
            for block in page_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            self._insert_text_span(new_page, span)

        # Agregamos el nombre elegido por el usuario a los metadatos internos
        self.new_doc.set_metadata({
            "title": output_name.replace(".pdf", ""),
            "producer": "InkSaver SaaS"
        })

        # Preparamos la salida en memoria
        output_stream = io.BytesIO()
        self.new_doc.save(output_stream)
        output_stream.seek(0)
        
        self.doc.close()
        self.new_doc.close()
        
        return output_stream

    def _insert_text_span(self, new_page, span):
        content = span["text"]
        if not content or not content.strip():
            return

        origin = span["origin"]
        size = span["size"]
        
        # Mapeo de fuentes estándar
        font_name = "helv" 
        if "bold" in span["font"].lower(): font_name = "hebo"
        if "italic" in span["font"].lower(): font_name = "heit"

        try:
            new_page.insert_text(
                origin,
                content,
                fontsize=size,
                fontname=font_name,
                color=(0, 0, 0)
            )
        except Exception:
            try:
                new_page.insert_text(
                    origin, content, fontsize=size, fontname="sans-serif", color=(0, 0, 0)
                )
            except:
                pass

# --- Bloque de prueba local ---
if __name__ == "__main__":
    input_file = "metodo-rama.pdf"  # Asegúrate de que este archivo exista en tu carpeta
    output_user_choice = "Mi_Archivo_Personalizado.pdf"
    
    print(f"🚀 Probando localmente con: {input_file}...")
    
    # Iniciamos pasándole la ruta y avisando que NO es un stream (is_stream=False)
    processor = PDFProcessor(input_file, is_stream=False)
    resultado = processor.clean_and_reconstruct(output_user_choice)
    
    # Guardamos el resultado del stream en un archivo físico para ver si funcionó
    with open(output_user_choice, "wb") as f:
        f.write(resultado.read())
        
    print(f"✅ ¡Listo! Revisa el archivo: {output_user_choice}")