import docx
import os
import zipfile

hub_dir = r"f:\MTN - Main Desktop\The National Mineral Intelligence Hub"
docx_path = os.path.join(hub_dir, "Team_and_Organization_Artwork_Showcase_POTRAZ_2026.docx")

if os.path.exists(docx_path):
    with zipfile.ZipFile(docx_path, 'r') as z:
        for fname in z.namelist():
            if fname.startswith("word/media/"):
                print("Media in docx:", fname, z.getinfo(fname).file_size)
