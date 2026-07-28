import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('Proposal-Skripsi-22166025- 19 Mei.docx') as z:
    with z.open('word/document.xml') as f:
        xml_content = f.read()

root = ET.fromstring(xml_content)
# The XML namespace for word
word_ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
text = []
for node in root.iter(word_ns + 't'):
    if node.text:
        text.append(node.text)

with open('proposal_text.txt', 'w', encoding='utf-8') as out:
    out.write(''.join(text))
