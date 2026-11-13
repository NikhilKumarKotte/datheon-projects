import zipfile
import re
import docx

with zipfile.ZipFile('MODEL-PROJECT-GUIDELINES -AIML -28-10-26.docx', 'r') as zin:
    with zipfile.ZipFile('model_guidelines_fixed.docx', 'w') as zout:
        for item in zin.infolist():
            buf = zin.read(item.filename)
            if item.filename == 'word/_rels/document.xml.rels':
                txt = buf.decode('utf-8')
                txt = re.sub(r'<Relationship[^>]*Target="NULL"[^>]*/>', '', txt)
                buf = txt.encode('utf-8')
            zout.writestr(item, buf)

doc = docx.Document('model_guidelines_fixed.docx')
print('Successfully loaded fixed docx! Paragraphs:', len(doc.paragraphs))
