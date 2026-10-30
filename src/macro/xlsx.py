"""Small XLSX values reader: no formula execution or optional dependency."""
import io
import posixpath
import zipfile
import xml.etree.ElementTree as ET

NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def workbook(payload):
    if not payload.startswith(b'PK'):raise ValueError('expected_official_xlsx_not_html')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if len(z.infolist())>400 or sum(i.file_size for i in z.infolist())>32*1024*1024:
            raise ValueError('xlsx_expansion_limit')
        if any('..' in i.filename.split('/') or i.filename.startswith('/') for i in z.infolist()):raise ValueError('invalid_xlsx_path')
        def xml(name):
            raw=z.read(name)
            if b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:raise ValueError('xlsx_xml_entities_prohibited')
            return ET.fromstring(raw)
        ss=[''.join(t.text or '' for t in n.iter('{'+NS['s']+'}t')) for n in xml('xl/sharedStrings.xml').findall('s:si',NS)] if 'xl/sharedStrings.xml' in z.namelist() else []
        rel={n.get('Id'):n.get('Target') for n in xml('xl/_rels/workbook.xml.rels') if n.get('TargetMode')!='External'}
        result={};total=0
        for sheet in xml('xl/workbook.xml').findall('s:sheets/s:sheet',NS):
            target=rel.get(sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'),'')
            name=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            if not name.startswith('xl/worksheets/') or '..' in name:raise ValueError('invalid_sheet_target')
            cells={}
            for c in xml(name).findall('.//s:sheetData/s:row/s:c',NS):
                total+=1
                if total>250000:raise ValueError('xlsx_cell_limit')
                v=c.find('s:v',NS);value=v.text if v is not None else ''.join(t.text or '' for t in c.findall('s:is//s:t',NS))
                if c.get('t')=='s' and value:value=ss[int(value)]
                if c.get('t') in ('e','b') and value:raise ValueError('xlsx_error_or_boolean_cell')
                # A formula without a cached value is missing, never evaluated.
                if value not in ('',None):cells[c.get('r')]=value
            if sheet.get('name') in result:raise ValueError('duplicate_sheet_name')
            result[sheet.get('name')]=cells
        return result
