# verificar_plantillas.py
import os

print("Verificando estructura de archivos:")
print(f"Directorio actual: {os.getcwd()}")

templates_dir = os.path.join(os.getcwd(), 'templates')
print(f"Carpeta templates: {templates_dir}")
print(f"¿Existe? {os.path.exists(templates_dir)}")

if os.path.exists(templates_dir):
    print("\nArchivos en templates:")
    for f in os.listdir(templates_dir):
        print(f"  - {f}")
else:
    print("\n❌ La carpeta 'templates' NO existe en el directorio actual")
    print("📌 Debes crearla y poner los archivos HTML allí")